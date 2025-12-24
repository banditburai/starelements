"""Integration helpers for StarHTML applications."""

from typing import Any, Type
from pathlib import Path

from .core import ElementDef
from .generator import generate_template, generate_registration_script


def get_component_assets(component_class: Type) -> dict[str, str]:
    """
    Get the HTML and JavaScript assets for a component.

    Args:
        component_class: A class decorated with @element

    Returns:
        Dict with 'template' and 'script' keys containing HTML strings

    Example:
        @element("my-comp")
        class MyComp:
            ...

        assets = get_component_assets(MyComp)
        # Include in page head:
        # assets["template"] + assets["script"]
    """
    if not hasattr(component_class, "_element_def"):
        raise ValueError(f"{component_class} is not decorated with @element")

    elem_def = component_class._element_def

    return {
        "template": generate_template(elem_def, component_class),
        "script": generate_registration_script(elem_def),
    }


def get_runtime_script(base_url: str = "/static/js") -> str:
    """
    Get the script tag to include the starelements runtime.

    Args:
        base_url: Base URL path for static files

    Returns:
        HTML script tag
    """
    return f'<script type="module" src="{base_url}/starelements.js"></script>'


def get_runtime_path() -> Path:
    """
    Get the path to the starelements.js runtime file.

    Returns:
        Path to the JavaScript runtime
    """
    return Path(__file__).parent / "static" / "starelements.js"


def register_with_app(app: Any, *component_classes: Type, route: str = "/static/js/starelements.js"):
    """
    Register starelements runtime with a FastHTML/Starlette app.

    This adds a route to serve the starelements.js runtime.

    Args:
        app: FastHTML or Starlette application
        component_classes: Component classes to register
        route: URL path for the runtime script

    Example:
        from fasthtml import FastHTML
        from starelements import register_with_app

        app = FastHTML()
        register_with_app(app, MyComponent, OtherComponent)
    """
    runtime_content = get_runtime_path().read_text()

    # Try to add route based on app type
    if hasattr(app, "route"):
        # FastHTML/Starlette style
        @app.route(route)
        def serve_runtime():
            from starlette.responses import Response
            return Response(
                content=runtime_content,
                media_type="application/javascript"
            )
    elif hasattr(app, "add_route"):
        # Alternative API
        def serve_runtime(request):
            from starlette.responses import Response
            return Response(
                content=runtime_content,
                media_type="application/javascript"
            )
        app.add_route(route, serve_runtime)


# Convenience function for head content
def starelements_head(*component_classes: Type, base_url: str = "/static/js") -> str:
    """
    Generate all head content for starelements components.

    Args:
        component_classes: Component classes decorated with @element
        base_url: Base URL for static files

    Returns:
        HTML string with all templates and runtime script

    Example:
        def page():
            return Html(
                Head(
                    NotStr(starelements_head(MyComponent, OtherComponent))
                ),
                Body(...)
            )
    """
    parts = []

    # Add runtime script
    parts.append(get_runtime_script(base_url))

    # Add templates for each component
    for cls in component_classes:
        assets = get_component_assets(cls)
        parts.append(assets["template"])

    return "\n".join(parts)
