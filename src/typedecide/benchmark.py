"""Package-owned benchmark cases and fixture loading utilities."""
from __future__ import annotations

import json
from dataclasses import dataclass
from importlib.resources import files
from typing import Any

from .types import Choice, Question


@dataclass(frozen=True)
class BenchmarkCase:
    """One package-owned benchmark item and its gold label.

    Parameters
    ----------
    id : str
        Stable case identifier, also used as the question ID.
    family : str
        Group used for per-family accuracy.
    state : str or dict or list
        Application state passed to the backend.
    question : Question
        The single typed question for this case.
    gold : str
        Option ID that the embedded state and rubric make true.
    tags : tuple of str
        Labels such as ``"clear"``, ``"negative"``, ``"boundary"``, or
        ``"no_match"``.
    """

    id: str
    family: str
    state: str | dict[str, Any] | list[Any]
    question: Question
    gold: str
    tags: tuple[str, ...]


def fixture_path(name: str = "test_cases.json"):
    """Locate a JSON fixture shipped inside the package.

    Parameters
    ----------
    name : str, optional
        File name under ``typedecide/fixtures``. The default is the benchmark suite.

    Returns
    -------
    Traversable
        Path-like resource for ``name``.
    """
    return files("typedecide").joinpath("fixtures", name)


def load_cases(name: str = "test_cases.json") -> list[BenchmarkCase]:
    """Load benchmark cases from a package fixture.

    Parameters
    ----------
    name : str, optional
        Fixture file name. The default is ``"test_cases.json"``.

    Returns
    -------
    list of BenchmarkCase
        Cases in file order. Question option order follows the fixture criteria.

    Raises
    ------
    ValueError
        If two cases share an ID.
    """
    records = json.loads(fixture_path(name).read_text())
    cases = []
    for record in records:
        question = Question(
            record["id"],
            record["primitive"],
            record["instructions"],
            tuple(Choice(item["label"], item["description"]) for item in record["criteria"]),
        )
        cases.append(BenchmarkCase(
            record["id"], record["family"], record["state"], question,
            record["gold_label"], tuple(record.get("tags", ())),
        ))
    identifiers = [case.id for case in cases]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("benchmark case IDs must be unique")
    return cases


def validate_real_world_suite() -> list[BenchmarkCase]:
    """Load the package benchmark and check its structural contract.

    The check requires a non-empty fixture, a family on every case, a
    supported primitive, and a gold label that is one of the options. It does
    not freeze the number of cases or families. Unique IDs and Noul order are
    checked while the fixture is loaded.

    Returns
    -------
    list of BenchmarkCase
        The loaded suite.

    Raises
    ------
    ValueError
        If any structural check fails.
    """
    cases = load_cases()
    if not cases:
        raise ValueError("benchmark fixture must contain cases")
    for case in cases:
        if not case.family:
            raise ValueError(f"{case.id} is missing a family")
        if case.question.type not in {"choice", "noul", "score"}:
            raise ValueError(f"{case.id} has unsupported primitive {case.question.type}")
        if case.gold not in case.question.option_ids:
            raise ValueError(f"{case.id} gold {case.gold!r} is not an option")
    return cases