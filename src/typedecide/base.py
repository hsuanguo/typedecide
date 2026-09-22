"""Protocol implemented by every typedecide backend."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Sequence

from .types import Question, Response


class DecisionBackend(ABC):
    """A loaded model that answers typed questions about one state.

    Attributes
    ----------
    name : str
        Short backend name used in artifacts and :func:`typedecide.load`.
    """

    name: str

    @abstractmethod
    def predict(self, state: str | dict[str, Any] | list[Any], questions: Sequence[Question]) -> Response:
        """Evaluate every question against one state.

        Parameters
        ----------
        state : str or dict or list
            Text or JSON-compatible application state. Structured state is
            preserved where the backend accepts it.
        questions : sequence of Question
            Questions that share ``state``. Each backend receives the same
            option IDs, descriptions, and canonical order.

        Returns
        -------
        Response
            One normalized answer per question, keyed by question ID.
        """

    def close(self) -> None:
        """Release model or client resources held by this backend."""