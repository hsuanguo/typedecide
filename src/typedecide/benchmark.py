"""Package-owned benchmark cases and fixture loading utilities."""
from __future__ import annotations

import json
from dataclasses import dataclass
from importlib.resources import files
from typing import Any

from .types import Choice, Question


@dataclass(frozen=True)
class BenchmarkCase:
    id: str
    family: str
    state: str | dict[str, Any] | list[Any]
    question: Question
    gold: str
    tags: tuple[str, ...]


def fixture_path(name: str = "test_cases.json"):
    return files("typedecide").joinpath("fixtures", name)


def load_cases(name: str = "test_cases.json") -> list[BenchmarkCase]:
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