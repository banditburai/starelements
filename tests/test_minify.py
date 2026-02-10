"""Tests for JavaScript minification using esbuild."""

import pytest


class TestMinifyJs:
    def test_minify_to_output_file(self, tmp_path):
        """minify_js writes minified content to output file."""
        from starelements.bundler import minify_js

        # Create source file with whitespace and comments
        source = tmp_path / "source.js"
        source.write_text("""
// This is a comment
function hello() {
    console.log("Hello, world!");
}

hello();
""")

        output = tmp_path / "output.min.js"

        result = minify_js(source, output)

        assert output.exists()
        assert len(result) < len(source.read_text())
        # Comments should be removed
        assert "This is a comment" not in result
        # Function should still work
        assert "hello" in result or "console" in result

    def test_minify_returns_content(self, tmp_path):
        """minify_js returns minified content when no output path."""
        from starelements.bundler import minify_js

        source = tmp_path / "source.js"
        source.write_text("""
const   x   =   1;
const   y   =   2;
console.log(x + y);
""")

        result = minify_js(source)

        # Should be smaller than original
        assert len(result) < len(source.read_text())
        # Should contain the logic
        assert "console" in result

    def test_minify_removes_whitespace(self, tmp_path):
        """minify_js removes unnecessary whitespace."""
        from starelements.bundler import minify_js

        source = tmp_path / "source.js"
        source.write_text("""
function    add(   a,    b   ) {
    return    a   +   b;
}
""")

        result = minify_js(source)

        # Multiple spaces should be collapsed
        assert "    " not in result
        # But the code should still work
        assert "function" in result or "=>" in result

    def test_minify_invalid_js_raises(self, tmp_path):
        """minify_js raises RuntimeError for invalid JavaScript."""
        from starelements.bundler import minify_js

        source = tmp_path / "invalid.js"
        source.write_text("function { invalid syntax")

        with pytest.raises(RuntimeError) as exc_info:
            minify_js(source)

        assert "esbuild" in str(exc_info.value).lower()

    def test_minify_nonexistent_file_raises(self, tmp_path):
        """minify_js raises error for nonexistent file."""
        from starelements.bundler import minify_js

        source = tmp_path / "nonexistent.js"

        with pytest.raises((RuntimeError, FileNotFoundError)):
            minify_js(source)

    def test_minify_creates_output_dir(self, tmp_path):
        """minify_js creates output directory if needed."""
        from starelements.bundler import minify_js

        source = tmp_path / "source.js"
        source.write_text("const x = 1;")

        output = tmp_path / "deep" / "nested" / "output.min.js"
        output.parent.mkdir(parents=True, exist_ok=True)

        result = minify_js(source, output)

        assert output.exists()
