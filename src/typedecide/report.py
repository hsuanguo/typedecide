"""Generate benchmark reports from completed raw backend artifacts."""
from __future__ import annotations

import hashlib
import html
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Sequence


def load_artifacts(paths: Sequence[Path]) -> list[dict[str, Any]]:
    if len(paths) < 2:
        raise ValueError("reporting requires artifacts from at least two backends")
    artifacts = [json.loads(path.read_text()) for path in paths]
    backends = [artifact.get("backend") for artifact in artifacts]
    if len(backends) != len(set(backends)):
        raise ValueError("report artifacts must have distinct backends")
    expected_cases = artifacts[0].get("cases")
    expected_repeats = artifacts[0].get("repeats")
    for artifact in artifacts:
        if artifact.get("status") != "complete":
            raise ValueError(f"artifact for {artifact.get('backend')} is not complete")
        if artifact.get("cases") != expected_cases or artifact.get("repeats") != expected_repeats:
            raise ValueError("report artifacts must have identical cases and repeat counts")
        expected_runs = len(expected_cases) * expected_repeats
        if len(artifact.get("runs", ())) != expected_runs:
            raise ValueError(f"artifact for {artifact.get('backend')} has incomplete runs")
    return artifacts


def _case_index(artifact: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {case["id"]: case for case in artifact["cases"]}


def _metrics(artifact: dict[str, Any]) -> dict[str, float | int | str]:
    brier_values, nll_values, score_errors, latencies, correct = [], [], [], [], 0
    for run in artifact["runs"]:
        answer = run["response"]["answers"][run["case_id"]]
        probabilities = answer["probabilities"]
        option_ids = answer["option_ids"]
        gold_index = option_ids.index(run["gold"])
        predicted = answer["selected"]
        correct += predicted == run["gold"]
        brier_values.append(sum((probability - float(index == gold_index)) ** 2 for index, probability in enumerate(probabilities)))
        nll_values.append(-math.log(max(probabilities[gold_index], 1e-12)))
        if run["primitive"] == "score":
            score_errors.append(abs(float(answer["score"]) - gold_index))
        latencies.append(float(run["response"]["latency_ms"]))
    total = len(artifact["runs"])
    return {
        "backend": artifact["backend"], "accuracy": correct / total, "brier": mean(brier_values),
        "nll": mean(nll_values), "score_mae": mean(score_errors) if score_errors else 0.0,
        "latency_ms": mean(latencies), "correct": correct, "total": total,
    }


def _accuracy_by(artifact: dict[str, Any], key: str) -> dict[str, float]:
    grouped: dict[str, list[bool]] = defaultdict(list)
    for run in artifact["runs"]:
        grouped[run[key]].append(run["response"]["answers"][run["case_id"]]["selected"] == run["gold"])
    return {name: mean(values) for name, values in sorted(grouped.items())}


def _case_summary(artifact: dict[str, Any]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for run in artifact["runs"]:
        grouped[run["case_id"]].append(run)
    summaries = {}
    for case_id, runs in grouped.items():
        answers = [run["response"]["answers"][case_id] for run in runs]
        option_ids = answers[0]["option_ids"]
        probabilities = tuple(mean(answer["probabilities"][index] for answer in answers) for index in range(len(option_ids)))
        selected = option_ids[max(range(len(probabilities)), key=probabilities.__getitem__)]
        top_labels = [answer["selected"] for answer in answers]
        summaries[case_id] = {"selected": selected, "probabilities": probabilities, "agreement": Counter(top_labels).most_common(1)[0][1] / len(top_labels)}
    return summaries


def _markdown(artifacts: list[dict[str, Any]], source_hash: str) -> str:
    metrics = [_metrics(artifact) for artifact in artifacts]
    cases = artifacts[0]["cases"]
    summaries = {artifact["backend"]: _case_summary(artifact) for artifact in artifacts}
    lines = [
        "# TypedDecide Benchmark Report", "",
        f"Authored {len(cases)}-case, {len({case['family'] for case in cases})}-family fixture; {len(artifacts)} backends; {artifacts[0]['repeats']} repeat(s). This is exploratory and does not establish broad model superiority.", "",
        "## Overall", "",
        "| Backend | Accuracy | Brier | NLL | Score MAE | Mean latency ms | Failures |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    lines.extend(
        f"| {metric['backend']} | {metric['accuracy']:.1%} | {metric['brier']:.4f} | {metric['nll']:.4f} | {metric['score_mae']:.4f} | {metric['latency_ms']:.1f} | 0 |"
        for metric in metrics
    )
    for dimension in ("family", "primitive"):
        lines.extend(["", f"## By {dimension.title()}", ""])
        groups = sorted({name for artifact in artifacts for name in _accuracy_by(artifact, dimension)})
        lines.append("| Group | " + " | ".join(artifact["backend"] for artifact in artifacts) + " |")
        lines.append("| --- | " + " | ".join("---:" for _ in artifacts) + " |")
        for group in groups:
            lines.append("| " + group + " | " + " | ".join(f"{_accuracy_by(artifact, dimension).get(group, 0):.1%}" for artifact in artifacts) + " |")
    lines.extend(["", "## Case Results", "", "| Case | Family | Gold | " + " | ".join(artifact["backend"] for artifact in artifacts) + " |", "| --- | --- | --- | " + " | ".join("---" for _ in artifacts) + " |"])
    for case in cases:
        values = []
        for artifact in artifacts:
            summary = summaries[artifact["backend"]][case["id"]]
            probability = max(summary["probabilities"])
            values.append(f"{'OK' if summary['selected'] == case['gold'] else 'ERR'} {summary['selected']} ({probability:.2f})")
        lines.append(f"| {case['id']} | {case['family']} | {case['gold']} | " + " | ".join(values) + " |")
    lines.extend(["", "## Method", "", f"Fixture/artifact provenance hash: `{source_hash}`.", "All metrics are derived from supplied raw JSON artifacts. Score MAE uses the normalized probability-weighted ordinal score. Latency is not hardware-equivalent across hosted and local backends."])
    return "\n".join(lines) + "\n"


def _html_report(markdown: str) -> str:
    escaped = html.escape(markdown)
    return f"""<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>TypedDecide Benchmark Report</title><style>body{{margin:0;background:#f4f2ec;color:#18211d;font:15px/1.5 'IBM Plex Sans','Liberation Sans',sans-serif}}main{{max-width:1160px;margin:auto;padding:36px 20px 64px}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:#fffefa;border:1px solid #d8d6ce;padding:20px}}h1{{font-family:Palatino,serif}}</style></head><body><main><h1>TypedDecide Benchmark Report</h1><pre>{escaped}</pre></main></body></html>"""


def write_report(artifacts: Sequence[Path], markdown_path: Path, html_path: Path) -> None:
    loaded = load_artifacts(artifacts)
    source_hash = hashlib.sha256(b"".join(path.read_bytes() for path in artifacts)).hexdigest()
    markdown = _markdown(loaded, source_hash)
    for path in (markdown_path, html_path):
        if path.exists():
            raise FileExistsError(f"refusing to overwrite existing output: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(markdown)
    from .html_renderer import render_html
    html_path.write_text(render_html(loaded, source_hash))


def merge_artifacts(artifacts: Sequence[Path], output: Path) -> None:
    """Combine compatible single-backend artifacts without changing their raw runs."""
    loaded = load_artifacts(artifacts)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({
        "status": "complete",
        "cases": loaded[0]["cases"],
        "repeats": loaded[0]["repeats"],
        "backends": [artifact["backend"] for artifact in loaded],
        "artifacts": loaded,
    }, indent=2) + "\n")