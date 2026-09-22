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


def fixture_path(name: str = "real_world.json"):
    return files("typedecide").joinpath("fixtures", name)


def load_cases(name: str = "real_world.json") -> list[BenchmarkCase]:
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
    families: dict[str, int] = {}
    for case in cases:
        families[case.family] = families.get(case.family, 0) + 1
    if len(cases) != 190 or len(families) != 19 or set(families.values()) != {10}:
        raise ValueError(f"expected 190 cases in 19 families of 10, got {families}")
    return cases