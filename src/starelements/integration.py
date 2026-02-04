"""Integration with StarHTML applications."""

from pathlib import Path
from typing import Type

from .decorator import get_registered_elements
from .generator import generate_template_ft


def get_static_path() -> Path:
    return Path(__file__).parent / "static"


def get_runtime_path() -> Path:
    return get_static_path() / "starelements.js"


def _generate_component_css(elem_def) -> list[str]:
    """Generate CSS rules for a single component."""
    name = elem_def.tag_name
    dims = [f"{k}:{v}" for k, v in elem_def.dimensions.items()]

    # Two-phase FOUC prevention:
    # - :not(:defined) hides before customElements.define() (web standard)
    # - :not([data-star-ready]) hides until connectedCallback completes setup
    hidden = f"{name}:not(:defined),{name}:not([data-star-ready])"
    hidden_before = f"{name}:not(:defined)::before,{name}:not([data-star-ready])::before"

    if elem_def.skeleton:
        return [
            f"{name}{{display:block}}",
            f"{hidden}{{visibility:hidden;contain:content;position:relative;{';'.join(dims)}}}",
            f"{hidden_before}{{"
            "content:'';visibility:visible;position:absolute;inset:0;"
            "background:linear-gradient(90deg,var(--star-skel-1) 0%,var(--star-skel-2) 50%,var(--star-skel-1) 100%);"
            "background-size:200% 100%;animation:star-shimmer 1.5s infinite;border-radius:4px}",
            f"{name}[data-star-ready]{{visibility:visible}}",
        ]
    return [
        f"{name}{{display:block}}",
        f"{hidden}{{visibility:hidden;contain:content;opacity:0;{';'.join(dims)}}}",
        f"{name}[data-star-ready]{{opacity:1;transition:opacity .15s}}",
    ]


_SKELETON_CSS = (
    ":root{--star-skel-1:#f0f0f0;--star-skel-2:#e8e8e8}"
    "[data-theme=dark]{--star-skel-1:#2a2a2a;--star-skel-2:#333}"
    "@media(prefers-color-scheme:dark){:root:not([data-theme=light]){--star-skel-1:#2a2a2a;--star-skel-2:#333}}"
    "@keyframes star-shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}"
)


def starelements_hdrs(*component_classes: Type, base_url: str = "/_pkg/starelements", debug: bool = False) -> tuple:
    """Generate header elements for starelements components.

    Single pass through components to collect all header data.

    Args:
        *component_classes: Component classes decorated with @element
        base_url: Base URL for serving static files (default: "/_pkg/starelements")
        debug: Enable debug mode with cache busting (default: False)

    Returns:
        Tuple of (Style, Script, Templates...) for inclusion in page headers.
    """
    from starhtml import Script, Style

    css_rules = []
    templates = []
    has_skeleton = False

    # Single pass through all components
    for cls in component_classes:
        if not hasattr(cls, "_element_def"):
            raise ValueError(f"{cls} is not decorated with @element")

        elem_def = cls._element_def

        if elem_def.skeleton:
            has_skeleton = True
        css_rules.extend(_generate_component_css(elem_def))
        templates.append(generate_template_ft(elem_def, cls))

    # Build hdrs
    if has_skeleton:
        css_rules.insert(0, _SKELETON_CSS)

    # Add cache busting in debug mode
    import time
    cache_bust = f"?v={int(time.time())}" if debug else ""

    return (
        Style("".join(css_rules)),
        Script(type="module", src=f"{base_url}/starelements.min.js{cache_bust}"),
        *templates,
    )


def register(app, *component_classes: Type, prefix: str = "/_pkg/starelements"):
    """
    Register starelements with a StarHTML app.

    Example:
        app, rt = star_app()
        register(app)  # Registers all @element components
    """
    if not component_classes:
        component_classes = tuple(get_registered_elements())
    if not component_classes:
        return

    hdrs = starelements_hdrs(*component_classes, base_url=prefix)

    app.register_package(
        "starelements",
        static_path=get_static_path(),
        hdrs=hdrs,
        prefix=prefix,
    )
