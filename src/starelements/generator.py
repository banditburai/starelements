"""Generate HTML templates and JavaScript for web components."""

from typing import Any, Type
from .core import ElementDef


def _python_to_js_value(value: Any) -> str:
    """Convert Python value to JavaScript literal."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return f"'{value}'"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict):
        items = ", ".join(f"{k}: {_python_to_js_value(v)}" for k, v in value.items())
        return f"{{{items}}}"
    if isinstance(value, list):
        items = ", ".join(_python_to_js_value(v) for v in value)
        return f"[{items}]"
    return str(value)


def _name_to_kebab(name: str) -> str:
    """Convert snake_case or camelCase to kebab-case."""
    import re
    # Handle camelCase
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', name)
    # Handle snake_case
    s2 = s1.replace('_', '-')
    return s2.lower()


def generate_template(elem_def: ElementDef, cls: Type) -> str:
    """
    Generate HTML template for a web component.

    Args:
        elem_def: Element definition from @element decorator
        cls: The decorated class

    Returns:
        HTML string containing <template data-star:name> element
    """
    parts = []

    # Opening template tag with data-star attribute
    attrs = [f'data-star:{elem_def.tag_name}']

    # Add data-props attributes
    for name, prop_def in elem_def.props.items():
        kebab_name = _name_to_kebab(name)
        codec = prop_def.to_codec_string()
        attrs.append(f'data-props:{kebab_name}="{codec}"')

    # Add data-import attributes
    for alias, url in elem_def.imports.items():
        attrs.append(f'data-import:{alias}="{url}"')

    # Add shadow DOM attribute if enabled
    if elem_def.shadow:
        attrs.append('data-shadow-open')

    parts.append(f'<template {" ".join(attrs)}>')

    # Script section for signals and setup
    script_parts = []

    # Initialize internal signals
    for name, sig_def in elem_def.signals.items():
        js_val = _python_to_js_value(sig_def.default)
        script_parts.append(f"    ${name} = {js_val};")

    # Add setup code if present
    if elem_def.setup_fn is not None:
        # Call setup method to get JS string
        instance = cls()
        setup_code = elem_def.setup_fn(instance)
        if setup_code:
            script_parts.append(f"    {setup_code.strip()}")

    if script_parts:
        parts.append("  <script>")
        parts.extend(script_parts)
        parts.append("  </script>")

    # Render template content
    if elem_def.render_fn is not None:
        instance = cls()
        content = elem_def.render_fn(instance)
        # Convert FT to string if needed
        if hasattr(content, '__ft__'):
            content = str(content)
        elif hasattr(content, 'to_xml'):
            content = content.to_xml()
        parts.append(f"  {content}")

    parts.append('</template>')

    return '\n'.join(parts)


def generate_registration_script(elem_def: ElementDef) -> str:
    """
    Generate JavaScript to include the starelements runtime.

    This is a placeholder - the actual runtime will be in a separate JS file.
    """
    return f'''<script type="module">
// starelements runtime will process data-star:{elem_def.tag_name} template
import {{ initStarElements }} from '/static/js/starelements.js';
initStarElements();
</script>'''
