"""Adapter for Laya's native typed-decision checkpoints."""
from __future__ import annotations

from time import perf_counter
from typing import Any, Sequence

from ..base import DecisionBackend
from ..types import Answer, Question, Response

DEFAULT_MODEL = "convaiinnovations/laya"
DEFAULT_SUBFOLDER = "typed-decisions"


class LayaBackend(DecisionBackend):
    """Laya adapter for the ``typed-decisions`` checkpoint. Requires the ``laya`` extra.

    Noul has no native criteria field, so the true and false meanings are
    written into the instructions. Returned probability maps are renormalized
    before they become an :class:`~typedecide.Answer`. Native confidence is
    kept and is not treated as a shared calibration.
    """

    name = "laya"

    def __init__(self, agent: Any, model: str, subfolder: str) -> None:
        self.agent = agent
        self.model = model
        self.subfolder = subfolder

    @classmethod
    def from_config(
        cls, model: str = DEFAULT_MODEL, subfolder: str = DEFAULT_SUBFOLDER,
        device: str | None = None, **config: Any,
    ):
        """Load a Laya checkpoint.

        Parameters
        ----------
        model : str, optional
            Hugging Face repo or local path. The default is
            ``convaiinnovations/laya``.
        subfolder : str, optional
            Checkpoint subfolder. The default is ``typed-decisions``.
        device : str or None, optional
            Torch device. ``None`` lets Laya choose.
        **config
            Forwarded to ``laya.load``.

        Returns
        -------
        LayaBackend
        """
        import laya

        return cls(laya.load(model, subfolder=subfolder, device=device, **config), model, subfolder)

    def predict(self, state: str | dict[str, Any] | list[Any], questions: Sequence[Question]) -> Response:
        """Evaluate questions with one Laya prediction.

        Parameters
        ----------
        state : str or dict or list
            Passed through to Laya.
        questions : sequence of Question
            Choice and Score criteria keep their descriptions. Noul meanings
            are appended to the instructions.

        Returns
        -------
        Response
            Normalized answers. Rounded provider distributions are rescaled to sum to one.

        Raises
        ------
        ValueError
            If a returned distribution has a nonpositive total.
        """
        native = {}
        for question in questions:
            if question.type == "choice":
                native[question.id] = {
                    "type": "choice", "instructions": question.instructions,
                    "criteria": {option.id: option.description for option in question.criteria},
                }
            elif question.type == "score":
                native[question.id] = {
                    "type": "score", "instructions": question.instructions,
                    "criteria": [option.description for option in question.criteria],
                }
            else:
                meanings = {option.id: option.description for option in question.criteria}
                native[question.id] = {
                    "type": "noul",
                    "instructions": (
                        f"{question.instructions}\n\nTrue means: {meanings['true']}\n"
                        f"False means: {meanings['false']}"
                    ),
                }
        started = perf_counter()
        result = self.agent.predict(state, native)
        latency_ms = (perf_counter() - started) * 1000
        answers = {}
        for question in questions:
            native_answer = result["answers"][question.id]
            if question.type == "noul":
                probabilities = (1.0 - float(native_answer["noul"]), float(native_answer["noul"]))
            elif question.type == "choice":
                probabilities = tuple(float(native_answer["probabilities"][option.id]) for option in question.criteria)
            else:
                probabilities = tuple(
                    float(native_answer["probabilities"].get(index, native_answer["probabilities"].get(str(index))))
                    for index in range(len(question.criteria))
                )
            total = sum(probabilities)
            if total <= 0:
                raise ValueError(f"Laya returned a nonpositive probability total for {question.id}")
            probabilities = tuple(value / total for value in probabilities)
            selected_index = max(range(len(probabilities)), key=probabilities.__getitem__)
            answers[question.id] = Answer(
                question.id, question.option_ids, probabilities, question.option_ids[selected_index],
                max(probabilities), native_answer.get("confidence"),
                sum(index * value for index, value in enumerate(probabilities))
                if question.type == "score" else None,
            )
        usage = result.get("usage", {})
        return Response(
            self.name, f"{self.model}/{self.subfolder}", str(result.get("model", self.model)),
            answers, latency_ms, usage.get("input_tokens"), usage.get("output_tokens"),
            {"noul_criteria": "rendered into instructions; Laya Noul has no criteria field"},
        )