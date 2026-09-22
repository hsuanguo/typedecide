"""Adapter for the existing this-that local model."""
from __future__ import annotations

import json
from time import perf_counter
from typing import Any, Sequence

from ..base import DecisionBackend
from ..types import Answer, Question, Response


class ThisThatBackend(DecisionBackend):
    """this-that adapter. Requires the ``thisthat`` extra.

    The model accepts text, so structured state is serialized as deterministic
    JSON with sorted keys. Each option is rendered as ``"{id}: {description}"``
    and the returned index is mapped back onto the original option order.
    """

    name = "thisthat"

    def __init__(self, decider: Any, model: str) -> None:
        self.decider = decider
        self.model = model

    @classmethod
    def from_config(cls, model: str = "flock-io/this-that-model-1.0", device: str = "auto", **kwargs: Any):
        """Load a this-that checkpoint.

        Parameters
        ----------
        model : str, optional
            Hugging Face repo or local path.
        device : str, optional
            ``"auto"``, ``"cuda"``, ``"mps"``, or ``"cpu"``.
        **kwargs
            Forwarded to ``TypedDecider.from_pretrained``.

        Returns
        -------
        ThisThatBackend
        """
        from thisthat import TypedDecider

        return cls(TypedDecider.from_pretrained(model, device=device, **kwargs), model)

    def predict(self, state: str | dict[str, Any] | list[Any], questions: Sequence[Question]) -> Response:
        """Evaluate questions in one this-that forward pass.

        Parameters
        ----------
        state : str or dict or list
            Text is passed through. A dict or list is serialized as JSON.
        questions : sequence of Question
            Options stay in submitted order.

        Returns
        -------
        Response
            Normalized answers. ``native_confidence`` is left unset.
        """
        rendered_state = state if isinstance(state, str) else json.dumps(
            state, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        )
        native_questions = [
            __import__("thisthat", fromlist=["Question"]).Question(
                question.instructions,
                [f"{option.id}: {option.description}" for option in question.criteria],
            )
            for question in questions
        ]
        started = perf_counter()
        decisions = self.decider.decide(rendered_state, native_questions)
        latency_ms = (perf_counter() - started) * 1000
        answers = {}
        for question, decision in zip(questions, decisions):
            probabilities = tuple(float(value) for value in decision.probabilities)
            answers[question.id] = Answer(
                question.id,
                question.option_ids,
                probabilities,
                question.option_ids[decision.index],
                max(probabilities),
                score=sum(index * value for index, value in enumerate(probabilities))
                if question.type == "score" else None,
            )
        return Response(self.name, self.model, self.model, answers, latency_ms)