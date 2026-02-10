# starelements

Custom web components, defined in Python, powered by Datastar signals.

You decorate a Python function, and it becomes a custom element. Each instance gets its own scoped signals — no JavaScript class boilerplate, no state collision between multiple instances on the same page.

## Why?

`starelements` gives you encapsulated custom elements where signals are scoped per instance and JS dependencies are declared with the component, not in your app headers. Define it once, `app.register()` it, and use it like any HTML element.

## Features

- **Decorator = component** — one `@element("tag-name")` and your function is a custom element. No class inheritance, no `connectedCallback`.
- **Scoped signals** — each component instance gets its own signal namespace. Two `<my-counter>` on the same page won't step on each other.
- **ESM imports built in** — pull in third-party JS via `imports={"chart": "https://esm.sh/chart.js@4"}`. No bundler config needed.
- **Light DOM by default** — your component's markup lives in the real DOM, so `<form>` submission, CSS selectors, and accessibility tools all just work. Shadow DOM is opt-in.
- **Skeleton loading** — set `height="400px", skeleton=True` and users see a shimmer placeholder until the component initializes. Prevents layout shift.

## Installation

Requires Python 3.12+ and [StarHTML](https://github.com/banditburai/starhtml).

```bash
pip install starelements
```

## Quick Start

A complete counter app — two instances with different initial values, each tracking its own state:

```python
from starhtml import Div, Button, Span, star_app, serve
from starelements import element, Local

@element("my-counter")
def Counter():
    return Div(
        (count := Local("count", 0)),
        (step := Local("step", 1)),
        Button("-", data_on_click=count.set(count - step)),
        Span(data_text=count),
        Button("+", data_on_click=count.set(count + step)),
    )

app, rt = star_app()
app.register(Counter)

@rt("/")
def home():
    return Div(Counter(count=10, step=5), Counter(count=0))

if __name__ == "__main__":
    serve()
```

Attributes you pass (`count=10, step=5`) become signal values inside that instance.

`Local` objects are signal references — `count + step` isn't evaluated in Python. It builds a JS expression, so `count.set(count + step)` produces `$$count = ($$count + $$step)` for the browser.

## Examples

### Skeleton loading

The `skeleton` option shows a shimmer placeholder while the component initializes, preventing layout shift:

```python
@element("heavy-chart", height="400px", skeleton=True,
         imports={"chart": "https://esm.sh/chart.js@4"})
def HeavyChart():
    return Div(
        Script('''
            new chart.Chart(refs('canvas'), {type: 'bar', data: {...}});
        '''),
        Canvas(data_ref="canvas", style="width:100%;height:100%;"),
    )
```

### Setup and cleanup with Script()

`Script()` inside your render tree runs once when the component connects. Use `onCleanup()` to tear down resources when the element is removed:

```python
@element("video-player")
def VideoPlayer():
    return Div(
        (playing := Local("playing", False)),
        Video(data_ref="video", src="/video.mp4"),
        Button("Play/Pause", data_on_click="$$playing = !$$playing"),
        Script('''
            const video = refs('video');
            effect(() => $$playing ? video.play() : video.pause());
            onCleanup(() => video.pause());
        '''),
    )
```

Inside `Script()`, imported modules are available by alias, signals are accessible as `$$name`, and `refs('name')` returns elements marked with `data_ref`.

For more complex examples, see:
- [`examples/counter.py`](examples/counter.py) — counter with step controls
- [`examples/waveform_editor.py`](examples/waveform_editor.py) — audio waveform editor using Peaks.js
- [`examples/codemirror/editor.py`](examples/codemirror/editor.py) — CodeMirror 6 with theme/language switching and complex import maps

## API Reference

### @element decorator

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | required | Custom element tag (must contain a hyphen, e.g. `my-counter`) |
| `shadow` | `bool` | `False` | Use Shadow DOM instead of Light DOM |
| `form_associated` | `bool` | `False` | Reserved for future form association support |
| `height` | `str \| None` | `None` | Shorthand for min-height; skeleton defaults to True when set |
| `width` | `str` | `"100%"` | Width dimension |
| `dimensions` | `dict \| None` | `None` | Full dimension dict (overrides height/width) |
| `skeleton` | `bool \| None` | `None` | Show shimmer placeholder while loading |
| `imports` | `dict \| None` | `None` | ESM imports — `{alias: specifier}` |
| `import_map` | `dict \| None` | `None` | Additional import map entries |
| `scripts` | `dict \| None` | `None` | UMD scripts — `{globalName: url}` |
| `events` | `list \| None` | `None` | Custom events the component emits |

### Registration

`app.register()` mounts static file routes and adds the component's CSS, import map, JS runtime, and templates to the app-wide headers (included on every page):

```python
app, rt = star_app()
app.register(Counter)              # single component
app.register(Counter, DatePicker)  # multiple at once
```

## CLI

`starelements` includes a CLI for bundling npm packages into ESM bundles using esbuild:

```bash
starelements bundle     # bundles packages listed in pyproject.toml [tool.starelements]
```

Configure packages in your `pyproject.toml`:

```toml
[tool.starelements]
bundle = ["chart.js@4", "@codemirror/state@6.4.1"]
```

## Development

```bash
uv sync --all-extras          # install dev + test dependencies
uv run scripts/build.py  # build JS runtime from TypeScript
uv run ruff check src/ tests/   # lint
uv run pytest tests/ -v          # run tests
```

The TypeScript runtime source lives in `typescript/`. The build script compiles it to `src/starelements/static/starelements.min.js`.

## License

[Apache 2.0](LICENSE)
