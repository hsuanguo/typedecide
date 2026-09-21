"""Backend-neutral typed-decision request and response values."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Mapping, Sequence

QuestionType = Literal["choice", "noul", "score"]


@dataclass(frozen=True)
class Choice:
    """One mutually exclusive option in a Choice question."""

    id: str
    description: str


Option = Choice


@dataclass(frozen=True)
class Question:
    """A typed question that every typedecide backend can evaluate."""

    id: str
    type: QuestionType
    instructions: str
    criteria: tuple[Choice, ...]

    def __post_init__(self) -> None:
        option_ids = self.option_ids
        if not self.id or not self.instructions:
            raise ValueError("question id and instructions must be non-empty")
        if len(option_ids) < 2 or len(option_ids) != len(set(option_ids)):
            raise ValueError("questions require at least two uniquely identified options")
        if self.type == "noul" and option_ids != ("false", "true"):
            raise ValueError("noul options must be ordered as false, true")

    @property
    def option_ids(self) -> tuple[str, ...]:
        return tuple(option.id for option in self.criteria)


def choice(id: str, instructions: str, criteria: Mapping[str, str]) -> Question:
    return Question(id, "choice", instructions, tuple(Choice(key, value) for key, value in criteria.items()))


def noul(id: str, instructions: str, *, true: str, false: str) -> Question:
    return Question(id, "noul", instructions, (Choice("false", false), Choice("true", true)))


def score(id: str, instructions: str, criteria: Sequence[str]) -> Question:
    return Question(
        id,
        "score",
        instructions,
        tuple(Choice(str(index), description) for index, description in enumerate(criteria)),
    )


@dataclass(frozen=True)
class Answer:
    """One normalized backend answer aligned to its question option order."""

    question_id: str
    option_ids: tuple[str, ...]
    probabilities: tuple[float, ...]
    selected: str
    top_probability: float
    native_confidence: float | None = None
    score: float | None = None

    def __post_init__(self) -> None:
        if len(self.option_ids) != len(self.probabilities):
            raise ValueError("option IDs and probabilities must have matching lengths")
        if self.selected not in self.option_ids:
            raise ValueError("selected option must exist in option IDs")
        if any(probability < 0 or probability > 1 for probability in self.probabilities):
            raise ValueError("probabilities must be between zero and one")
        if abs(sum(self.probabilities) - 1) > 1e-6:
            raise ValueError("probabilities must sum to one")


@dataclass(frozen=True)
class Response:
    """Normalized answers and execution metadata from one backend request."""

    backend: str
    requested_model: str
    resolved_model: str
    answers: Mapping[str, Answer]
    latency_ms: float
    input_tokens: int | None = None
    output_tokens: int | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)