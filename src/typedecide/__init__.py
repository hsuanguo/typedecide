"""One Python API for typed decisions, and a benchmark shared by every backend.

Build questions with :func:`choice`, :func:`noul`, and :func:`score`, then
evaluate them through :func:`load`. Every backend returns the same
:class:`Response`. The package fixture is loaded with :func:`load_cases`.
"""

from .base import DecisionBackend
from .benchmark import (
    BenchmarkCase,
    fixture_path,
    load_cases,
    validate_real_world_suite,
)
from .registry import available_backends, load
from .types import Answer, Option, Question, Response, choice, noul, score

__all__ = [
    "Answer",
    "BenchmarkCase",
    "DecisionBackend",
    "fixture_path",
    "Option",
    "Question",
    "Response",
    "available_backends",
    "choice",
    "load",
    "load_cases",
    "noul",
    "score",
    "validate_real_world_suite",
]
