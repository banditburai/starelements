"""Example: Simple counter component using starelements."""

from starelements import element, prop, signal


@element("my-counter")
class Counter:
    """
    A simple counter component demonstrating starelements basics.

    Props:
        initial: Starting count value
        step: Amount to increment/decrement by

    Events:
        change: Fired when count changes with new value
    """

    # Props - observed attributes
    initial: int = prop(default=0)
    step: int = prop(default=1, ge=1)

    # Internal signals
    count: int = signal(0)

    # Events
    class Events:
        change: int

    def render(self):
        """Render the counter UI."""
        return """
        <div class="counter">
            <button data-on:click="$count -= $step">-</button>
            <span data-text="$count" class="count-display"></span>
            <button data-on:click="$count += $step">+</button>
        </div>
        """

    def setup(self) -> str:
        """Initialize count from initial prop."""
        return '''
            // Initialize count from initial prop
            $count = parseInt(el.getAttribute('initial') || '0', 10);

            // Watch for count changes and emit event
            effect(() => {
                el.emit('change', $count);
            });
        '''


if __name__ == "__main__":
    from starelements import get_component_assets

    # Show generated template
    assets = get_component_assets(Counter)
    print("=== Template ===")
    print(assets["template"])

    # Show usage
    print("\n=== Usage Example ===")
    print(Counter(initial=5, step=2, on_change="console.log('Count:', evt.detail)"))
