"""Tests for HTML/JS template generation."""

import pytest
from starelements import element, prop, signal
from starelements.generator import generate_template, generate_registration_script


class TestGenerateTemplate:
    def test_basic_template_structure(self):
        """Template has correct data-star attribute."""
        @element("test-comp")
        class TestComp:
            def render(self):
                return "<div>Hello</div>"

        html = generate_template(TestComp._element_def, TestComp)
        assert 'data-star:test-comp' in html
        assert '<template' in html
        assert '</template>' in html

    def test_props_generate_data_props(self):
        """Props become data-props attributes."""
        @element("prop-comp")
        class PropComp:
            count: int = prop(default=0, ge=0)
            title: str = prop(required=True)

        html = generate_template(PropComp._element_def, PropComp)
        assert 'data-props:count="int|min:0|=0"' in html
        assert 'data-props:title="string|required!"' in html

    def test_imports_generate_data_import(self):
        """Imports become data-import attributes."""
        @element("import-comp")
        class ImportComp:
            imports = {"Peaks": "https://esm.sh/peaks.js"}

        html = generate_template(ImportComp._element_def, ImportComp)
        assert 'data-import:Peaks="https://esm.sh/peaks.js"' in html

    def test_signals_in_setup_script(self):
        """Internal signals are initialized in setup script."""
        @element("signal-comp")
        class SignalComp:
            is_playing: bool = signal(False)
            count: int = signal(0)

        html = generate_template(SignalComp._element_def, SignalComp)
        assert '$is_playing = false' in html
        assert '$count = 0' in html

    def test_setup_code_included(self):
        """Setup method code is included."""
        @element("setup-comp")
        class SetupComp:
            def setup(self) -> str:
                return "console.log('hello');"

        html = generate_template(SetupComp._element_def, SetupComp)
        assert "console.log('hello');" in html


class TestGenerateRegistrationScript:
    def test_generates_script_tag(self):
        """Registration generates script element."""
        @element("reg-comp")
        class RegComp:
            pass

        script = generate_registration_script(RegComp._element_def)
        assert '<script' in script
        assert '</script>' in script
