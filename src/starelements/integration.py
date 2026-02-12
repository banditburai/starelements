import time
from pathlib import Path
from typing import Any

from .core import ElementDef

_CODEC_MAP = {int: "int", float: "float", str: "string", bool: "boolean"}


def get_static_path() -> Path:
    return Path(__file__).parent / "static"


def get_runtime_path() -> Path:
    return get_static_path() / "starelements.js"


def _value_to_js(value: Any) -> str:
    # Prevent Datastar's expression preprocessor from mangling @ and $ chars
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        from starhtml.datastar import _safe_js_string

        return _safe_js_string(value)
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict):
        return "{" + ", ".join(f"{k}: {_value_to_js(v)}" for k, v in value.items()) + "}"
    if isinstance(value, list):
        return "[" + ", ".join(_value_to_js(v) for v in value) + "]"
    return str(value)


def _extract_signals_from_ft(ft: Any, component_signals: list | None = None) -> tuple[Any, dict[str, Any]]:
    from starhtml.datastar import Expr, Signal

    signals: dict[str, Any] = {}
    seen_ids = set()

    if component_signals:
        for sig in component_signals:
            if sig._id not in seen_ids:
                signals[sig._name] = {"initial": sig._initial, "type": sig.type_}
                seen_ids.add(sig._id)

    def collect_from_node(node: Any):
        if hasattr(node, "__signals_found"):
            for sig in node.__signals_found:
                if isinstance(sig, Signal) and sig._id not in seen_ids:
                    if isinstance(sig._initial, Expr):
                        continue  # Computed signals handled by StarHTML's data-computed:* attrs
                    signals[sig._name] = {"initial": sig._initial, "type": sig.type_}
                    seen_ids.add(sig._id)
            delattr(node, "__signals_found")

        if hasattr(node, "children"):
            for child in node.children:
                collect_from_node(child)

    collect_from_node(ft)
    return ft, signals


def generate_template_ft(elem_def: ElementDef, cls: type):
    from starhtml import Template

    from .signals import collect_local_signals

    children = []
    signals = {}

    if elem_def.render_fn:
        with collect_local_signals() as component_signals:
            ft = elem_def.render_fn()
        cleaned_ft, signals = _extract_signals_from_ft(ft, component_signals)
        if cleaned_ft is not None:
            children.append(cleaned_ft)

    attrs = {f"data-star:{elem_def.tag_name}": True}
    attrs.update({f"data-import:{k}": v for k, v in elem_def.imports.items()})
    attrs.update({f"data-script:{k}": v for k, v in elem_def.scripts.items()})
    if elem_def.shadow:
        attrs["data-shadow-open"] = True
    for name, info in signals.items():
        codec = _CODEC_MAP.get(info["type"], "string")
        # parseCodec expects raw values, not JS-quoted strings
        match info["initial"]:
            case None:
                raw = ""
            case bool() as b:
                raw = "true" if b else "false"
            case str() as s:
                raw = s
            case int() | float():
                raw = str(info["initial"])
            case dict() | list():
                raw = _value_to_js(info["initial"])
            case other:
                raw = str(other)
        attrs[f"data-signal:{name}"] = f"{codec}|={raw}"

    return Template(*children, **attrs)


def _generate_component_css(elem_def: ElementDef) -> list[str]:
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


def _starelements_hdrs(*component_classes: type, pkg_prefix: str = "/_pkg", debug: bool = False) -> tuple:
    from starhtml import Script, Style

    css_rules = []
    templates = []
    has_skeleton = False

    for cls in component_classes:
        if not hasattr(cls, "_element_def"):
            raise ValueError(f"{cls} is not decorated with @element")

        elem_def = cls._element_def

        if elem_def.skeleton:
            has_skeleton = True
        css_rules.extend(_generate_component_css(elem_def))
        templates.append(generate_template_ft(elem_def, cls))

    hdrs = []
    if css_rules:
        if has_skeleton:
            css_rules.insert(0, _SKELETON_CSS)
        hdrs.append(Style("".join(css_rules)))

    cache_bust = f"?v={int(time.time())}" if debug else ""

    hdrs.append(Script(type="module", src=f"{pkg_prefix}/starelements/starelements.min.js{cache_bust}"))
    hdrs.extend(templates)

    return tuple(hdrs)
