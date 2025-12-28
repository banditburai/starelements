"""Generate HTML templates for web components."""

import re
from typing import Any, Type

from .core import ElementDef

_SIGNAL_PATTERN = re.compile(r'(\w+):\s*([^,}]+)')
_CODEC_MAP = {int: "int", float: "float", str: "string", bool: "boolean"}


def _parse_js_value(s: str) -> tuple[Any, type]:
    """Parse a JS literal string into Python value and type."""
    s = s.strip()
    if s == 'true': return True, bool
    if s == 'false': return False, bool
    if s == 'null': return None, type(None)
    if s.startswith(("'", '"')): return s.strip("'\""), str
    try:
        return (float(s), float) if '.' in s else (int(s), int)
    except ValueError:
        return s, str


def _value_to_js(value: Any) -> str:
    """Convert Python value to JS literal."""
    if value is None: return "null"
    if isinstance(value, bool): return "true" if value else "false"
    if isinstance(value, str): return f"'{value}'"
    if isinstance(value, (int, float)): return str(value)
    if isinstance(value, dict):
        return "{" + ", ".join(f"{k}: {_value_to_js(v)}" for k, v in value.items()) + "}"
    if isinstance(value, list):
        return "[" + ", ".join(_value_to_js(v) for v in value) + "]"
    return str(value)


def _clean_ft_internals(node: Any):
    """Remove __signals_found attr that prevents deepcopy."""
    if hasattr(node, "__dict__"):
        node.__dict__.pop("__signals_found", None)
    if hasattr(node, "children"):
        for child in node.children:
            _clean_ft_internals(child)


def _extract_signals_from_ft(ft: Any) -> tuple[Any, dict[str, Any]]:
    """Extract signals from FT tree, returning cleaned tree and signal definitions."""
    try:
        from starhtml.datastar import Signal, Expr
    except ImportError:
        from starhtml import Signal, Expr

    signals: dict[str, Any] = {}

    def walk(node: Any) -> Any:
        if isinstance(node, Signal):
            # Skip computed signals - StarHTML adds data-computed:* attrs automatically
            if isinstance(node._initial, Expr):
                return None
            signals[node._name] = {"initial": node._initial, "type": node.type_}
            return None

        if hasattr(node, "tag") and hasattr(node, "children"):
            if data_signals := (node.attrs or {}).get("data-signals"):
                for m in _SIGNAL_PATTERN.finditer(str(data_signals)):
                    val, typ = _parse_js_value(m.group(2))
                    signals[m.group(1)] = {"initial": val, "type": typ}
                del node.attrs["data-signals"]

            node.children = [c for child in node.children if (c := walk(child)) is not None]
            _clean_ft_internals(node)
            return node

        if isinstance(node, (list, tuple)):
            return [c for item in node if (c := walk(item)) is not None]

        return node

    return walk(ft), signals


def generate_template_ft(elem_def: ElementDef, cls: Type):
    """Generate FT Template element for a web component."""
    from starhtml import Template, Script

    children = []
    signals = {}

    if elem_def.render_fn:
        cleaned_ft, signals = _extract_signals_from_ft(elem_def.render_fn(cls()))
        if cleaned_ft is not None:
            children.append(cleaned_ft)

    if elem_def.setup_fn and (code := elem_def.setup_fn(cls()).strip()):
        children.insert(0, Script(code))

    attrs = {f"data-star:{elem_def.tag_name}": True}
    attrs.update({f"data-import:{k}": v for k, v in elem_def.imports.items()})
    attrs.update({f"data-script:{k}": v for k, v in elem_def.scripts.items()})
    if elem_def.shadow:
        attrs["data-shadow-open"] = True
    for name, info in signals.items():
        codec = _CODEC_MAP.get(info["type"], "string")
        attrs[f"data-signal:{name}"] = f"{codec}|={_value_to_js(info['initial'])}"

    return Template(*children, **attrs)
