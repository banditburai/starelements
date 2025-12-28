"""Example: Simple counter component using starelements."""

from starhtml import star_app, Div, Button, Span, Signal
from starelements import element, starelements_hdrs, register_with_app


@element("my-counter")
class Counter:
    """A simple counter component demonstrating starelements basics."""

    def render(self):
        """Render the counter UI."""
        count = Signal("count", 0)
        step = Signal("step", 1)
        return Div(
            count, step,
            Button("-", data_on_click=count.set(count - step)),
            Span(data_text=count, style="padding:0 1rem;font-size:1.5rem;"),
            Button("+", data_on_click=count.set(count + step)),
            style="display:flex;align-items:center;gap:0.5rem;",
        )


if __name__ == "__main__":
    from fastcore.xml import to_xml
    from starelements.generator import generate_template_ft

    # Show generated template
    ft = generate_template_ft(Counter._element_def, Counter)
    print("=== Template ===")
    print(to_xml(ft))

    # Show usage
    print("\n=== Usage Example ===")
    print(Counter(count=5, step=2))
