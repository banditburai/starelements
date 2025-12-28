"""Tests for HTML/JS template generation."""

import pytest
from fastcore.xml import to_xml
from starelements import element
from starelements.generator import generate_template_ft


class TestGenerateTemplateFt:
    def test_basic_template_structure(self):
        """Template has correct data-star attribute."""
        @element("test-comp")
        class TestComp:
            def render(self):
                from starhtml import Div
                return Div("Hello")

        ft = generate_template_ft(TestComp._element_def, TestComp)
        html = to_xml(ft)
        assert 'data-star:test-comp' in html
        assert '<template' in html
        assert '</template>' in html

    def test_signals_become_template_attrs(self):
        """Signals are extracted and become data-signal attributes on template."""
        @element("signal-comp")
        class SignalComp:
            def render(self):
                from starhtml import Div, Signal
                count = Signal("count", 0)
                return Div(count, "Content")

        ft = generate_template_ft(SignalComp._element_def, SignalComp)
        html = to_xml(ft)
        assert 'data-signal:count="int|=0"' in html

    def test_imports_generate_data_import(self):
        """Imports become data-import attributes."""
        @element("import-comp")
        class ImportComp:
            imports = {"peaks": "https://esm.sh/peaks.js"}

        ft = generate_template_ft(ImportComp._element_def, ImportComp)
        html = to_xml(ft)
        assert 'data-import:peaks="https://esm.sh/peaks.js"' in html

    def test_setup_code_included(self):
        """Setup method code is included."""
        @element("setup-comp")
        class SetupComp:
            def setup(self) -> str:
                return "console.log('hello');"

        ft = generate_template_ft(SetupComp._element_def, SetupComp)
        html = to_xml(ft)
        assert "console.log('hello');" in html

    def test_returns_ft_with_template_tag(self):
        """generate_template_ft returns FT with tag='template'."""
        @element("ft-comp")
        class FtComp:
            def render(self):
                from starhtml import Div
                return Div("Hello")

        ft = generate_template_ft(FtComp._element_def, FtComp)
        assert ft.tag == "template"

    def test_ft_has_data_star_attr(self):
        """FT Template has data-star:tag-name attribute."""
        @element("attr-comp")
        class AttrComp:
            def render(self):
                from starhtml import Div
                return Div("Hello")

        ft = generate_template_ft(AttrComp._element_def, AttrComp)
        assert ft.attrs.get("data-star:attr-comp") is True
