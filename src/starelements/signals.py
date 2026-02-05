"""Component-scoped signals for starelements.

ComponentSignal creates signals that are isolated to a single component instance.
In JavaScript setup code, these use the $$ prefix (e.g., $$count) and are
automatically namespaced to prevent collisions between component instances.

Design Notes:
    ComponentSignal inherits from Signal to preserve Expr functionality (operator
    overloading, .set(), .if_(), etc.). It uses `_ref_only=True` to exclude itself
    from StarHTML's page-level signal pipeline - the signal declaration is handled
    by starelements' template generator instead, which outputs `data-signal:*`
    attributes on the <template> element.

    The collection mechanism uses contextvars (not threading.local) for proper
    async compatibility. Signals auto-register when created inside a
    `collect_component_signals()` context.

Usage:
    @element("my-counter")
    class Counter:
        def render(self):
            count = ComponentSignal("count", 0)  # -> $$count in JS
            return Div(Span(data_text=count))

        def setup(self):
            return '''
                effect(() => {
                    console.log('Local:', $$count);   // Component-local
                    console.log('Global:', $theme);   // Page-level
                });
            '''
"""

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

from starhtml.datastar import Signal

# Context variable for collecting ComponentSignals during render.
# Uses contextvars (not threading.local) for async compatibility.
_signal_collector: ContextVar[list | None] = ContextVar("signal_collector", default=None)


@contextmanager
def collect_component_signals():
    """Context manager to collect ComponentSignals created during render.

    Used by the generator to capture component-scoped signals. These signals
    use `_ref_only=True` which excludes them from StarHTML's page-level
    processing - starelements handles their declaration via template attributes.

    Example:
        with collect_component_signals() as signals:
            ft = component.render()
        # signals now contains all ComponentSignals created during render
    """
    collector: list = []
    token = _signal_collector.set(collector)
    try:
        yield collector
    finally:
        _signal_collector.reset(token)


class ComponentSignal(Signal):
    """Component-scoped signal using $$ prefix.

    Unlike regular Signal, ComponentSignal:
    - Uses $$ prefix in JavaScript (e.g., $$count)
    - Gets namespaced per component instance at runtime (e.g., $$count -> $_star_my_comp_id0_count)
    - Declaration handled by template generator, not StarHTML's page-level pipeline

    Uses `_ref_only=True` because signal declaration is handled externally - the
    starelements template generator outputs `data-signal:name="type|=default"`
    attributes on the `<template>` element. This is the same pattern used by
    StarHTML plugins (where declaration is in JS) and route handlers (where
    signals already exist on the page).

    This enables isolated state per component instance while still allowing
    access to global signals via the standard $ prefix.
    """

    def __init__(
        self,
        name: str,
        initial: Any = None,
        ifmissing: bool = True,
        type_: type | None = None,
    ):
        # Don't register in global registry - namespaced names are
        # determined at runtime in the browser
        super().__init__(
            name=name,
            initial=initial,
            ifmissing=ifmissing,
            type_=type_,
            namespace=None,
            _ref_only=True,
        )
        # Override _js to use $$ prefix for component-local signals
        self._js = f"$${self._name}"

        # Register with collector if we're in a render context
        if (collector := _signal_collector.get()) is not None:
            collector.append(self)

    def to_js(self) -> str:
        """Return $$ prefix for component-local signal."""
        return f"$${self._name}"

    @property
    def is_component_signal(self) -> bool:
        """Identify this as a component signal for generator."""
        return True
