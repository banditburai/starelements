from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

from starhtml.datastar import Signal

# contextvars (not threading.local) for async compatibility
_signal_collector: ContextVar[list | None] = ContextVar("signal_collector", default=None)


@contextmanager
def collect_local_signals():
    collector: list = []
    token = _signal_collector.set(collector)
    try:
        yield collector
    finally:
        _signal_collector.reset(token)


class Local(Signal):
    """Component-scoped signal using $$ prefix (e.g., $$count)."""

    def __init__(
        self,
        name: str,
        initial: Any = None,
        ifmissing: bool = True,
        type_: type | None = None,
    ):
        # Don't register in global registry — namespaced names are
        # determined at runtime in the browser
        super().__init__(
            name=name,
            initial=initial,
            ifmissing=ifmissing,
            type_=type_,
            namespace=None,
            _ref_only=True,
        )
        self._js = f"$${self._name}"

        if (collector := _signal_collector.get()) is not None:
            collector.append(self)
