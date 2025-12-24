"""Helper functions for defining component props and signals."""

from dataclasses import dataclass
from typing import Any


@dataclass
class PropMarker:
    """Marker class for prop() definitions in element classes."""

    default: Any = None
    required: bool = False
    ge: float | None = None
    le: float | None = None
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None


@dataclass
class SignalMarker:
    """Marker class for signal() definitions in element classes."""

    default: Any = None


def prop(
    default: Any = None,
    *,
    required: bool = False,
    ge: float | None = None,
    le: float | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
    pattern: str | None = None,
) -> PropMarker:
    """
    Define a component prop (observed attribute).

    Args:
        default: Default value if not provided
        required: Whether the prop is required
        ge: Minimum value (>=) for numeric props
        le: Maximum value (<=) for numeric props
        min_length: Minimum length for string props
        max_length: Maximum length for string props
        pattern: Regex pattern for string validation

    Returns:
        PropMarker for use in @element decorated class

    Example:
        @element("my-counter")
        class MyCounter:
            count: int = prop(default=0, ge=0)
            label: str = prop(required=True)
    """
    return PropMarker(
        default=default,
        required=required,
        ge=ge,
        le=le,
        min_length=min_length,
        max_length=max_length,
        pattern=pattern,
    )


def signal(default: Any = None) -> SignalMarker:
    """
    Define an internal component signal (scoped to instance).

    Args:
        default: Initial value of the signal

    Returns:
        SignalMarker for use in @element decorated class

    Example:
        @element("my-player")
        class MyPlayer:
            is_playing: bool = signal(False)
            current_time: float = signal(0.0)
    """
    return SignalMarker(default=default)
