"""Tests for component-scoped signals."""

from starelements.signals import Local, collect_local_signals


class TestLocal:
    def test_local_has_double_dollar_prefix(self):
        """Local signal JS reference uses $$ prefix."""
        with collect_local_signals():
            sig = Local("count", 0)
        assert str(sig) == "$$count"

    def test_local_preserves_initial(self):
        """Local signal stores initial value."""
        with collect_local_signals():
            sig = Local("name", "hello")
        assert sig._initial == "hello"

    def test_local_default_initial_is_none(self):
        """Local signal defaults to None initial."""
        with collect_local_signals():
            sig = Local("empty")
        assert sig._initial is None

    def test_local_with_type(self):
        """Local signal accepts explicit type."""
        with collect_local_signals():
            sig = Local("count", 0, type_=int)
        assert sig.type_ is int


class TestCollectLocalSignals:
    def test_collector_captures_signals(self):
        """collect_local_signals captures all Local signals created in context."""
        with collect_local_signals() as signals:
            a = Local("a", 1)
            b = Local("b", 2)
        assert len(signals) == 2
        assert signals[0] is a
        assert signals[1] is b

    def test_collector_empty_when_none_created(self):
        """collect_local_signals returns empty list when no signals created."""
        with collect_local_signals() as signals:
            pass
        assert signals == []

    def test_collector_isolates_contexts(self):
        """Nested collectors don't leak signals."""
        with collect_local_signals() as outer:
            Local("outer", 1)
            with collect_local_signals() as inner:
                Local("inner", 2)
        assert len(outer) == 1
        assert len(inner) == 1
        assert outer[0]._name == "outer"
        assert inner[0]._name == "inner"

    def test_no_collector_doesnt_error(self):
        """Creating Local outside collector context doesn't raise."""
        sig = Local("orphan", 42)
        assert str(sig) == "$$orphan"
