"""Backend-neutral typed-decision request and response values."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Mapping, Sequence

QuestionType = Literal["choice", "noul", "score"]


@dataclass(frozen=True)
class Choice:
    """One mutually exclusive option.

    Parameters
    ----------
    id : str
        Stable option identifier. Returned probabilities line up with this ID.
    description : str
        Meaning of the option. Put changing source text here, not in ``id``.

    Notes
    -----
    ``Option`` is an alias of this class.
    """

    id: str
    description: str


Option = Choice


@dataclass(frozen=True)
class Question:
    """A typed question that every backend evaluates the same way.

    Parameters
    ----------
    id : str
        Key under which the answer is returned.
    type : {"choice", "noul", "score"}
        Question primitive.
    instructions : str
        Question text shown to the backend.
    criteria : tuple of Choice
        Options in canonical order. A Noul question is ``false``, then
        ``true``. A Score rubric runs from low to high.

    Raises
    ------
    ValueError
        If the ID or instructions are empty, fewer than two unique options
        are given, or a Noul question is not ordered ``false``, ``true``.
    """

    id: str
    type: QuestionType
    instructions: str
    criteria: tuple[Choice, ...]

    def __post_init__(self) -> None:
        option_ids = self.option_ids
        if not self.id or not self.instructions:
            raise ValueError("question id and instructions must be non-empty")
        if len(option_ids) < 2 or len(option_ids) != len(set(option_ids)):
            raise ValueError(
                "questions require at least two uniquely identified options"
            )
        if self.type == "noul" and option_ids != ("false", "true"):
            raise ValueError("noul options must be ordered as false, true")

    @property
    def option_ids(self) -> tuple[str, ...]:
        """Option identifiers in submitted criterion order.

        Returns
        -------
        tuple of str
            Criterion IDs. For a Noul question this is ``("false", "true")``.
        """
        return tuple(option.id for option in self.criteria)


def choice(id: str, instructions: str, criteria: Mapping[str, str]) -> Question:
    """Build a Choice question that selects one named option.

    Parameters
    ----------
    id : str
        Question identifier.
    instructions : str
        Question text.
    criteria : mapping of str to str
        Option ID to description. Insertion order is the canonical order.

    Returns
    -------
    Question
        A question whose ``type`` is ``"choice"``.
    """
    return Question(
        id,
        "choice",
        instructions,
        tuple(Choice(key, value) for key, value in criteria.items()),
    )


def noul(id: str, instructions: str, *, true: str, false: str) -> Question:
    """Build a Noul question with explicit false and true meanings.

    Parameters
    ----------
    id : str
        Question identifier.
    instructions : str
        Proposition to judge.
    true : str
        Meaning of the true outcome.
    false : str
        Meaning of the false outcome.

    Returns
    -------
    Question
        A question whose options are ordered ``false``, then ``true``.
    """
    return Question(
        id, "noul", instructions, (Choice("false", false), Choice("true", true))
    )


def score(id: str, instructions: str, criteria: Sequence[str]) -> Question:
    """Build a Score question from an ordered rubric.

    Parameters
    ----------
    id : str
        Question identifier.
    instructions : str
        Question text.
    criteria : sequence of str
        Rubric level descriptions from low to high. Option IDs are the
        string indices ``"0"``, ``"1"``, and so on.

    Returns
    -------
    Question
        A question whose ``type`` is ``"score"``.
    """
    return Question(
        id,
        "score",
        instructions,
        tuple(
            Choice(str(index), description)
            for index, description in enumerate(criteria)
        ),
    )


@dataclass(frozen=True)
class Answer:
    """One normalized backend answer, aligned to its question option order.

    Parameters
    ----------
    question_id : str
        ID of the question this answer belongs to.
    option_ids : tuple of str
        Option IDs in the same order as ``probabilities``.
    probabilities : tuple of float
        Distribution over ``option_ids``. Values lie in ``[0, 1]`` and sum to one.
    selected : str
        Option ID with the highest probability.
    top_probability : float
        Probability of ``selected``.
    native_confidence : float or None, optional
        Provider-specific confidence. Definitions differ across backends, so
        do not compare this value between providers.
    score : float or None, optional
        Probability-weighted rubric index for a Score question. ``None`` for
        Choice and Noul.

    Raises
    ------
    ValueError
        If the probability vector does not match the options, ``selected`` is
        unknown, a probability is outside ``[0, 1]``, or the probabilities do
        not sum to one.
    """

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
        if any(
            probability < 0 or probability > 1 for probability in self.probabilities
        ):
            raise ValueError("probabilities must be between zero and one")
        if abs(sum(self.probabilities) - 1) > 1e-6:
            raise ValueError("probabilities must sum to one")


@dataclass(frozen=True)
class Response:
    """Normalized answers and execution metadata from one backend request.

    Parameters
    ----------
    backend : str
        Backend name, such as ``"jev"`` or ``"laya"``.
    requested_model : str
        Model identifier requested by the caller.
    resolved_model : str
        Model identifier reported by the provider.
    answers : mapping of str to Answer
        Answers keyed by question ID.
    latency_ms : float
        Wall time for this request, in milliseconds. Hosted round-trip time
        and local inference time are not hardware-equivalent.
    input_tokens : int or None, optional
        Provider-reported input tokens, when the backend records them.
    output_tokens : int or None, optional
        Provider-reported output tokens, when the backend records them.
    metadata : mapping, optional
        Backend-specific details that are not part of the shared answer contract.
    """

    backend: str
    requested_model: str
    resolved_model: str
    answers: Mapping[str, Answer]
    latency_ms: float
    input_tokens: int | None = None
    output_tokens: int | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
