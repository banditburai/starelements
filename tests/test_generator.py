"""Tests for HTML/JS template generation."""

from fastcore.xml import to_xml

from starelements import element
from starelements.integration import generate_template_ft


class TestGenerateTemplateFt:
    def test_basic_template_structure(self):
        """Template has correct data-star attribute."""

        @element("test-comp")
        def TestComp():
            from starhtml import Div

            return Div("Hello")

        ft = generate_template_ft(TestComp._element_def, TestComp)
        html = to_xml(ft)
        assert "data-star:test-comp" in html
        assert "<template" in html
        assert "</template>" in html

    def test_signals_become_template_attrs(self):
        """Signals are extracted and become data-signal attributes on template."""

        @element("signal-comp")
        def SignalComp():
            from starhtml import Div, Signal

            count = Signal("count", 0)
            return Div("Content", data_bind=count)

        ft = generate_template_ft(SignalComp._element_def, SignalComp)
        assert ft.attrs.get("data-signal:count") == "int|=0"

        html = to_xml(ft)
        assert 'data-signal:count="int|=0"' in html

    def test_imports_generate_data_import(self):
        """Imports become data-import attributes."""

        @element("import-comp", imports={"peaks": "https://esm.sh/peaks.js"})
        def ImportComp():
            return None

        ft = generate_template_ft(ImportComp._element_def, ImportComp)
        html = to_xml(ft)
        assert 'data-import:peaks="https://esm.sh/peaks.js"' in html

    def test_scripts_generate_data_script(self):
        """Scripts become data-script attributes (for UMD loading)."""

        @element("script-comp", scripts={"peaks": "https://unpkg.com/peaks.js@3/dist/peaks.js"})
        def ScriptComp():
            return None

        ft = generate_template_ft(ScriptComp._element_def, ScriptComp)
        html = to_xml(ft)
        assert 'data-script:peaks="https://unpkg.com/peaks.js@3/dist/peaks.js"' in html

    def test_returns_ft_with_template_tag(self):
        """generate_template_ft returns FT with tag='template'."""

        @element("ft-comp")
        def FtComp():
            from starhtml import Div

            return Div("Hello")

        ft = generate_template_ft(FtComp._element_def, FtComp)
        assert ft.tag == "template"

    def test_ft_has_data_star_attr(self):
        """FT Template has data-star:tag-name attribute."""

        @element("attr-comp")
        def AttrComp():
            from starhtml import Div

            return Div("Hello")

        ft = generate_template_ft(AttrComp._element_def, AttrComp)
        assert ft.attrs.get("data-star:attr-comp") is True

    def test_with_local_signals(self):
        """Local signals generate data-signal attrs."""

        @element("local-sig-comp")
        def LocalSigComp():
            from starhtml import Div

            from starelements import Local

            count = Local("count", 0)
            return Div(count, data_text=count)

        ft = generate_template_ft(LocalSigComp._element_def, LocalSigComp)
        assert ft.attrs.get("data-signal:count") == "int|=0"

    def test_inline_script_in_render(self):
        """Script() in render tree generates script element in template."""

        @element("inline-script-comp")
        def InlineScriptComp():
            from starhtml import Div, Script

            return Div(
                Script("console.log('inline setup');"),
                "Content",
            )

        ft = generate_template_ft(InlineScriptComp._element_def, InlineScriptComp)
        html = to_xml(ft)
        assert "console.log('inline setup');" in html
        assert "<script" in html
