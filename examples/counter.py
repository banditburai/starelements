"""Example: Simple counter component using starelements."""

from starhtml import H1, Button, Div, Span, Style, serve, star_app

from starelements import Local, element


@element("my-counter")
def Counter():
    """Counter with component-local state ($$count, $$step)."""
    return Div(
        (count := Local("count", 0)),  # -> $$count in JS
        (step := Local("step", 1)),
        Button("-", data_on_click=count.set(count - step), cls="counter-btn decrement"),
        Span(data_text=count, cls="counter-display"),
        Button("+", data_on_click=count.set(count + step), cls="counter-btn increment"),
        cls="counter-row",
    )


app, rt = star_app()
app.register(Counter)


@rt("/")
def home():
    return Div(
        Style("""
            *, *::before, *::after {
                box-sizing: border-box;
            }
            body {
                margin: 0;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                             "Helvetica Neue", Arial, sans-serif;
                background: #f8f9fa;
                color: #1a1a2e;
                -webkit-font-smoothing: antialiased;
            }
            .page {
                max-width: 480px;
                margin: 4rem auto;
                padding: 0 1.5rem;
            }
            .page-title {
                font-size: 1.5rem;
                font-weight: 600;
                letter-spacing: -0.025em;
                margin: 0 0 2rem 0;
                color: #111;
            }
            .counters {
                display: flex;
                flex-direction: column;
                gap: 1rem;
            }
            my-counter {
                display: block;
            }
            .counter-row {
                display: flex;
                align-items: center;
                gap: 0;
                background: #fff;
                border: 1px solid #e2e5e9;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.02);
                transition: box-shadow 0.15s ease;
            }
            .counter-row:hover {
                box-shadow: 0 4px 12px rgba(0,0,0,0.06), 0 1px 3px rgba(0,0,0,0.04);
            }
            .counter-btn {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 3rem;
                height: 3rem;
                border: none;
                background: transparent;
                font-size: 1.25rem;
                font-weight: 500;
                color: #555;
                cursor: pointer;
                transition: background 0.12s ease, color 0.12s ease;
                user-select: none;
                flex-shrink: 0;
            }
            .counter-btn:hover {
                background: #f0f1f3;
                color: #111;
            }
            .counter-btn:active {
                background: #e4e6e9;
            }
            .counter-btn:focus-visible {
                outline: 2px solid #4f8ff7;
                outline-offset: -2px;
                z-index: 1;
            }
            .counter-btn.decrement {
                border-right: 1px solid #e2e5e9;
            }
            .counter-btn.increment {
                border-left: 1px solid #e2e5e9;
            }
            .counter-display {
                flex: 1;
                text-align: center;
                font-size: 1.375rem;
                font-weight: 600;
                font-variant-numeric: tabular-nums;
                color: #1a1a2e;
                padding: 0 0.75rem;
                letter-spacing: -0.01em;
            }
        """),
        H1("Counter", cls="page-title"),
        Div(
            Counter(count=10, step=5),
            Counter(count=0, step=1),
            cls="counters",
        ),
        cls="page",
    )


if __name__ == "__main__":
    serve()
