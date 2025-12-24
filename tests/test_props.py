"""Tests for prop() and signal() helper functions."""

import pytest
from starelements import prop, signal
from starelements.props import PropMarker, SignalMarker


class TestProp:
    def test_prop_returns_marker(self):
        """prop() returns a PropMarker instance."""
        p = prop(default=0)
        assert isinstance(p, PropMarker)

    def test_prop_with_constraints(self):
        """prop() stores constraint values."""
        p = prop(default=0, ge=0, le=100)
        assert p.default == 0
        assert p.ge == 0
        assert p.le == 100

    def test_prop_required(self):
        """prop(required=True) marks as required."""
        p = prop(required=True)
        assert p.required is True
        assert p.default is None


class TestSignal:
    def test_signal_returns_marker(self):
        """signal() returns a SignalMarker instance."""
        s = signal(False)
        assert isinstance(s, SignalMarker)

    def test_signal_stores_default(self):
        """signal() stores default value."""
        s = signal(42)
        assert s.default == 42
