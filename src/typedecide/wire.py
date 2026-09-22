"""Convert TypeSafe System One JSON to typedecide questions and back."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from .types import Question, Response, choice, noul, score


class WireError(ValueError):
    """A System One request that fails validation.

    Parameters
    ----------
    message : str
        What is wrong with the request.
    field : str or None
        Dotted path of the offending field, when one applies.
    """

    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.field = field


def decision_confidence(probabilities: Sequence[float]) -> float:
    """Collapse a distribution into a confidence in ``[0, 1]``.

    Parameters
    ----------
    probabilities : sequence of float
        A distribution over two or more options.

    Returns
    -------
    float
        ``(n * peak - 1) / (n - 1)``, clamped to ``[0, 1]``. A single peak of
        ``1`` is ``1``. A uniform distribution is ``0``.
    """
    count = len(probabilities)
    if count < 2:
        return 1.0
    peak = max(probabilities)
    value = (count * peak - 1) / (count - 1)
    return max(0.0, min(1.0, value))


def parse_system_one(
    payload: Mapping[str, Any],
) -> tuple[str | dict[str, Any] | list[Any], tuple[Question, ...]]:
    """Parse a ``POST /v1/systemone`` body into state and questions.

    Parameters
    ----------
    payload : mapping
        Official request body. ``model`` is accepted and ignored.

    Returns
    -------
    tuple
        State, then questions in submitted order.

    Raises
    ------
    WireError
        If the body is not a valid System One request.
    """
    if "model" in payload and not isinstance(payload["model"], str):
        raise WireError("model must be a string", "model")
    if "state" not in payload:
        raise WireError("state is required", "state")
    state = payload["state"]
    if not isinstance(state, (str, dict, list)):
        raise WireError("state must be a string, object, or array", "state")
    raw_questions = payload.get("questions")
    if not isinstance(raw_questions, dict) or not raw_questions:
        raise WireError("questions must be a non-empty object", "questions")
    questions = tuple(
        _parse_question(str(question_id), body)
        for question_id, body in raw_questions.items()
    )
    return state, questions


def encode_system_one(
    response: Response, questions: Sequence[Question]
) -> dict[str, Any]:
    """Encode a backend response as a System One response body.

    Parameters
    ----------
    response : Response
        Normalized backend response.
    questions : sequence of Question
        Questions in the order their answers should appear.

    Returns
    -------
    dict
        ``model``, ``answers``, and ``usage`` in the official shapes.
    """
    answers = {
        question.id: _encode_answer(question, response.answers[question.id])
        for question in questions
    }
    return {
        "model": response.resolved_model,
        "answers": answers,
        "usage": {
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
        },
    }


def _parse_question(question_id: str, body: Any) -> Question:
    field = f"questions.{question_id}"
    if not question_id:
        raise WireError("question id must be non-empty", "questions")
    if not isinstance(body, dict):
        raise WireError("question must be an object", field)
    kind = body.get("type")
    if kind not in {"noul", "choice", "score"}:
        raise WireError("type must be noul, choice, or score", f"{field}.type")
    if "instructions" not in body:
        raise WireError("instructions are required", f"{field}.instructions")
    instructions = _json_text(body["instructions"], f"{field}.instructions")
    if not instructions:
        raise WireError("instructions must be non-empty", f"{field}.instructions")
    try:
        if kind == "noul":
            return _parse_noul(question_id, instructions, body.get("criteria"), field)
        if kind == "choice":
            return _parse_choice(question_id, instructions, body.get("criteria"), field)
        return _parse_score(question_id, instructions, body.get("criteria"), field)
    except WireError:
        raise
    except ValueError as error:
        raise WireError(str(error), f"{field}.criteria") from error


def _parse_noul(
    question_id: str, instructions: str, criteria: Any, field: str
) -> Question:
    true = "yes"
    false = "no"
    if criteria is not None:
        if not isinstance(criteria, dict):
            raise WireError("noul criteria must be an object", f"{field}.criteria")
        if "true" in criteria:
            true = _json_text(criteria["true"], f"{field}.criteria.true")
        if "false" in criteria:
            false = _json_text(criteria["false"], f"{field}.criteria.false")
    return noul(question_id, instructions, true=true, false=false)


def _parse_choice(
    question_id: str, instructions: str, criteria: Any, field: str
) -> Question:
    if not isinstance(criteria, dict):
        raise WireError("choice criteria must be an object", f"{field}.criteria")
    if len(criteria) > 255:
        raise WireError("choice accepts at most 255 options", f"{field}.criteria")
    options = {}
    for option_id, description in criteria.items():
        if not isinstance(option_id, str) or not option_id:
            raise WireError("option id must be non-empty", f"{field}.criteria")
        if description is None:
            options[option_id] = ""
        else:
            options[option_id] = _json_text(
                description, f"{field}.criteria.{option_id}"
            )
    return choice(question_id, instructions, options)


def _parse_score(
    question_id: str, instructions: str, criteria: Any, field: str
) -> Question:
    if not isinstance(criteria, list):
        raise WireError("score criteria must be an array", f"{field}.criteria")
    if len(criteria) > 10:
        raise WireError("score accepts at most 10 levels", f"{field}.criteria")
    levels = [
        _json_text(level, f"{field}.criteria.{index}")
        for index, level in enumerate(criteria)
    ]
    return score(question_id, instructions, levels)


def _json_text(value: Any, field: str) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    raise WireError("must be a string, object, or array", field)


def _encode_answer(question: Question, answer: Any) -> dict[str, Any]:
    if question.type == "noul":
        true_index = answer.option_ids.index("true")
        return {"type": "noul", "noul": answer.probabilities[true_index]}
    by_id = dict(zip(answer.option_ids, answer.probabilities, strict=True))
    probabilities = {option.id: by_id[option.id] for option in question.criteria}
    confidence = decision_confidence(tuple(probabilities.values()))
    if question.type == "choice":
        return {
            "type": "choice",
            "choice": answer.selected,
            "probabilities": probabilities,
            "confidence": confidence,
        }
    if answer.score is None:
        raise ValueError("score answer is missing a weighted score")
    return {
        "type": "score",
        "score": answer.score,
        "legend": {option.id: option.description for option in question.criteria},
        "probabilities": probabilities,
        "confidence": confidence,
    }
