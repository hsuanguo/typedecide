"""Run package-owned typedecide benchmark fixtures through one unified backend."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from . import available_backends, load, validate_real_world_suite
from .report import merge_artifacts, write_report


def parser() -> argparse.ArgumentParser:
    """Build the ``typedecide-benchmark`` argument parser.

    Returns
    -------
    argparse.ArgumentParser
        Parser with ``validate``, ``run``, ``report``, and ``merge`` subcommands.
    """
    command = argparse.ArgumentParser(description=__doc__)
    subcommands = command.add_subparsers(dest="command", required=True)
    subcommands.add_parser("validate", help="validate package-owned benchmark fixtures")
    run = subcommands.add_parser(
        "run", help="run one backend over the package benchmark"
    )
    run.add_argument("--backend", choices=available_backends(), required=True)
    run.add_argument("--repeats", type=int, default=1)
    run.add_argument("--device", default="auto")
    run.add_argument("--output", type=Path, required=True)
    report = subcommands.add_parser(
        "report", help="generate Markdown and HTML from backend artifacts"
    )
    report.add_argument("--artifacts", type=Path, nargs="+", required=True)
    report.add_argument("--markdown", type=Path, required=True)
    report.add_argument("--html", type=Path, required=True)
    merge = subcommands.add_parser(
        "merge", help="merge compatible backend artifacts into a manifest"
    )
    merge.add_argument("--artifacts", type=Path, nargs="+", required=True)
    merge.add_argument("--output", type=Path, required=True)
    return command


def main() -> int:
    """Run the benchmark command selected on the command line.

    Returns
    -------
    int
        Process status code. ``0`` means the command finished.

    Raises
    ------
    ValueError
        If ``--repeats`` is not positive.
    FileExistsError
        If ``run`` would overwrite an existing artifact.
    """
    args = parser().parse_args()
    cases = validate_real_world_suite()
    if args.command == "validate":
        print(
            f"valid: {len(cases)} cases across {len({case.family for case in cases})} families"
        )
        return 0
    if args.command == "report":
        write_report(args.artifacts, args.markdown, args.html)
        print(f"wrote {args.markdown} and {args.html}")
        return 0
    if args.command == "merge":
        merge_artifacts(args.artifacts, args.output)
        print(f"wrote {args.output}")
        return 0
    if args.repeats < 1:
        raise ValueError("repeats must be positive")
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {args.output}")

    backend_config = {}
    if args.backend in {"thisthat", "semif"}:
        backend_config["device"] = args.device
    elif args.backend == "laya" and args.device != "auto":
        backend_config["device"] = args.device
    backend = load(args.backend, **backend_config)
    runs = []
    try:
        backend.predict(cases[0].state, (cases[0].question,))
        for repeat in range(args.repeats):
            for case in cases:
                response = backend.predict(case.state, (case.question,))
                runs.append(
                    {
                        "case_id": case.id,
                        "family": case.family,
                        "primitive": case.question.type,
                        "gold": case.gold,
                        "repeat": repeat,
                        "response": asdict(response),
                    }
                )
    finally:
        backend.close()
    artifact = {
        "status": "complete",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "backend": args.backend,
        "repeats": args.repeats,
        "cases": [
            {"id": case.id, "family": case.family, "gold": case.gold} for case in cases
        ],
        "runs": runs,
        "typedecide": importlib.metadata.version("typedecide"),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, indent=2) + "\n")
    correct = sum(
        run["response"]["answers"][run["case_id"]]["selected"] == run["gold"]
        for run in runs
    )
    print(f"wrote {args.output}: {correct}/{len(runs)} correct")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
