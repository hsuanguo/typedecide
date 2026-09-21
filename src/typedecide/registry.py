"""Lazy backend loading so optional SDKs are never imported by default."""
from __future__ import annotations

from typing import Any


_BACKENDS = {
    "thisthat": ("typedecide.backends.thisthat", "ThisThatBackend", "typedecide[thisthat]"),
    "jev": ("typedecide.backends.jev", "JevBackend", "typedecide[jev]"),
    "semif": ("typedecide.backends.semif", "SemIfBackend", "typedecide[semif]"),
    "laya": ("typedecide.backends.laya", "LayaBackend", "typedecide[laya]"),
}


def available_backends() -> tuple[str, ...]:
    return tuple(_BACKENDS)


def load(backend: str, **config: Any):
    """Load a named backend without importing other optional backend dependencies."""
    if backend not in _BACKENDS:
        raise ValueError(f"unknown backend {backend!r}; choose from {available_backends()!r}")
    module_name, class_name, extra = _BACKENDS[backend]
    try:
        module = __import__(module_name, fromlist=[class_name])
    except ImportError as error:
        raise ImportError(f"Backend {backend!r} is unavailable. Install {extra}.") from error
    return getattr(module, class_name).from_config(**config)