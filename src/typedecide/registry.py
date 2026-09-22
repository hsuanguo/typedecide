"""Lazy backend loading so optional SDKs are never imported by default."""

from __future__ import annotations

from typing import Any


_BACKENDS = {
    "thisthat": (
        "typedecide.backends.thisthat",
        "ThisThatBackend",
        "typedecide[thisthat]",
    ),
    "jev": ("typedecide.backends.jev", "JevBackend", "typedecide[jev]"),
    "semif": ("typedecide.backends.semif", "SemIfBackend", "typedecide[semif]"),
    "laya": ("typedecide.backends.laya", "LayaBackend", "typedecide[laya]"),
}


def available_backends() -> tuple[str, ...]:
    """List backend names accepted by :func:`load`.

    Returns
    -------
    tuple of str
        ``"thisthat"``, ``"jev"``, ``"semif"``, and ``"laya"``, in that order.
    """
    return tuple(_BACKENDS)


def load(backend: str, **config: Any):
    """Load one backend without importing the other optional SDKs.

    Parameters
    ----------
    backend : {"thisthat", "jev", "semif", "laya"}
        Backend to load.
    **config
        Passed to that backend's ``from_config``. Common keys are ``model``
        and, for local backends, ``device``.

    Returns
    -------
    DecisionBackend
        A loaded backend. Call ``close`` when finished.

    Raises
    ------
    ValueError
        If ``backend`` is not a known name.
    ImportError
        If that backend's optional extra is not installed.
    """
    if backend not in _BACKENDS:
        raise ValueError(
            f"unknown backend {backend!r}; choose from {available_backends()!r}"
        )
    module_name, class_name, extra = _BACKENDS[backend]
    try:
        module = __import__(module_name, fromlist=[class_name])
    except ImportError as error:
        raise ImportError(
            f"Backend {backend!r} is unavailable. Install {extra}."
        ) from error
    return getattr(module, class_name).from_config(**config)
