"""Protocol implemented by every typedecide backend."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Sequence

from .types import Question, Response


class DecisionBackend(ABC):
    """Load once, then evaluate one state against one or more typed questions."""

    name: str

    @abstractmethod
    def predict(self, state: str | dict[str, Any] | list[Any], questions: Sequence[Question]) -> Response:
        """Return normalized answers in the input question order."""

    def close(self) -> None:
        """Release optional backend resources."""