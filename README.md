# starelements

Python-native web components for StarHTML/Datastar.

## Overview

`starelements` provides a Python decorator-based API for defining custom web components that integrate seamlessly with StarHTML and Datastar's reactive signal system.

## Installation

```bash
pip install starelements
```

## Quick Start

```python
from starelements import element, prop, signal

@element("my-counter")
class MyCounter:
    # Props - observed attributes with validation
    initial: int = prop(default=0, ge=0)

    # Signals - internal reactive state
    count: int = signal(0)

    def render(self):
        return Div(
            Span(data_text="$count"),
            Button("+", data_on_click="$count++"),
        )

    def setup(self) -> str:
        return "$count = $initial;"

# Use like any StarHTML component
MyCounter(initial=5, on_change="console.log(evt.detail)")
```

## Features

- **Python-native API**: Define components with Python classes and decorators
- **Datastar integration**: Automatic signal scoping and reactivity
- **Validation**: Props support type validation via Datastar codecs
- **Lifecycle management**: `setup()` and `onCleanup()` hooks
- **External imports**: Easy integration with third-party JS libraries
- **Light DOM default**: Better accessibility and form integration

## License

MIT
