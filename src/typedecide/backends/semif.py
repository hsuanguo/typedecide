"""Adapter for SemIf's pinned direct categorical scorer."""
from __future__ import annotations

from typing import Any, Sequence

from ..base import DecisionBackend
from ..types import Answer, Question, Response

DEFAULT_MODEL = "Qwen/Qwen3.5-4B"
DEFAULT_REVISION = "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"


class SemIfBackend(DecisionBackend):
    name = "semif"

    def __init__(self, model: Any, tokenizer: Any, metadata: dict[str, Any]) -> None:
        self.model = model
        self.tokenizer = tokenizer
        self.metadata = metadata

    @classmethod
    def from_config(
        cls, model: str = DEFAULT_MODEL, revision: str = DEFAULT_REVISION,
        device: str = "auto", dtype: str = "bfloat16", **_: Any,
    ):
        from semif_phase1.core import load_causal_model

        loaded_model, tokenizer, metadata = load_causal_model(model, revision, device, dtype)
        return cls(loaded_model, tokenizer, metadata)

    def predict(self, state: str | dict[str, Any] | list[Any], questions: Sequence[Question]) -> Response:
        from semif_phase1.direct import score

        answers = {}
        total_latency_ms = 0.0
        total_tokens = 0
        for question in questions:
            row = {
                "id": question.id,
                "state": state,
                "question": question.instructions,
                "options": [
                    {"id": option.id, "description": option.description}
                    for option in question.criteria
                ],
            }
            result = score(self.model, self.tokenizer, row, self.metadata)
            probabilities = tuple(float(value) for value in result["probabilities"])
            selected_index = max(range(len(probabilities)), key=probabilities.__getitem__)
            answers[question.id] = Answer(
                question.id, question.option_ids, probabilities, question.option_ids[selected_index],
                max(probabilities), score=sum(index * value for index, value in enumerate(probabilities))
                if question.type == "score" else None,
            )
            total_latency_ms += float(result["total_seconds"]) * 1000
            total_tokens += int(result["input_tokens"])
        resolved = f"{self.metadata['source']}@{self.metadata['revision']}"
        return Response(
            self.name, self.metadata["source"], resolved, answers, total_latency_ms, total_tokens,
            metadata={"probability_status": "conditional option score; uncalibrated as decision confidence"},
        )