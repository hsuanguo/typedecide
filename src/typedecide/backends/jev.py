"""Adapter for TypeSafe Jev's native Choice, Noul, and Score primitives."""

from __future__ import annotations

from time import perf_counter
from typing import Any, Sequence

from ..base import DecisionBackend
from ..types import Answer, Question, Response


class JevBackend(DecisionBackend):
    """TypeSafe Jev adapter. Requires the ``jev`` extra and ``TYPESAFE_API_KEY``.

    Choice, Noul, and Score are sent as native TypeSafe questions. Noul
    probabilities are ``(1 - noul, noul)`` so they stay in ``false``, ``true``
    order. Score uses the ordered rubric descriptions, and ``Answer.score`` is
    their probability-weighted index.
    """

    name = "jev"

    def __init__(self, client: Any, model: str) -> None:
        self.client = client
        self.model = model

    @classmethod
    def from_config(
        cls, model: str = "jev-1.13.0", timeout: float = 30.0, **config: Any
    ):
        """Open a TypeSafe client for a pinned Jev model.

        Parameters
        ----------
        model : str, optional
            Versioned model ID. The default is ``"jev-1.13.0"``.
        timeout : float, optional
            Request timeout in seconds.
        **config
            Forwarded to ``TypeSafeClient``.

        Returns
        -------
        JevBackend
        """
        from typesafe_sdk import TypeSafeClient

        return cls(TypeSafeClient(model=model, timeout=timeout, **config), model)

    def predict(
        self, state: str | dict[str, Any] | list[Any], questions: Sequence[Question]
    ) -> Response:
        """Evaluate questions with one System One request.

        Parameters
        ----------
        state : str or dict or list
            Passed through as TypeSafe state.
        questions : sequence of Question
            Mapped to native Choice, Noul, and Score questions.

        Returns
        -------
        Response
            Normalized answers. ``resolved_model`` is the ID the service reports.
        """
        from typesafe_sdk import Choice, Noul, NoulCriteria, Score

        native = {}
        for question in questions:
            if question.type == "choice":
                native[question.id] = Choice(
                    instructions=question.instructions,
                    criteria={
                        option.id: option.description for option in question.criteria
                    },
                )
            elif question.type == "score":
                native[question.id] = Score(
                    instructions=question.instructions,
                    criteria=[option.description for option in question.criteria],
                )
            else:
                meanings = {
                    option.id: option.description for option in question.criteria
                }
                native[question.id] = Noul(
                    instructions=question.instructions,
                    criteria=NoulCriteria(
                        true=meanings["true"], false=meanings["false"]
                    ),
                )
        started = perf_counter()
        result = self.client.system_one(state=state, questions=native, model=self.model)
        latency_ms = (perf_counter() - started) * 1000
        answers = {}
        for question in questions:
            native_answer = result.answers[question.id]
            if question.type == "noul":
                probabilities = (
                    1.0 - float(native_answer.noul),
                    float(native_answer.noul),
                )
                confidence = None
            elif question.type == "choice":
                probabilities = tuple(
                    float(native_answer.probabilities[option.id])
                    for option in question.criteria
                )
                confidence = float(native_answer.confidence)
            else:
                probabilities = tuple(
                    float(native_answer.probabilities[index])
                    for index in range(len(question.criteria))
                )
                confidence = float(native_answer.confidence)
            selected_index = max(
                range(len(probabilities)), key=probabilities.__getitem__
            )
            answers[question.id] = Answer(
                question.id,
                question.option_ids,
                probabilities,
                question.option_ids[selected_index],
                max(probabilities),
                confidence,
                sum(
                    index * probability
                    for index, probability in enumerate(probabilities)
                )
                if question.type == "score"
                else None,
            )
        return Response(
            self.name,
            self.model,
            result.model,
            answers,
            latency_ms,
            result.usage.input_tokens,
            result.usage.output_tokens,
            {"request_id": getattr(result, "request_id", None)},
        )

    def close(self) -> None:
        """Close the TypeSafe client."""
        self.client.close()
