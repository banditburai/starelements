"""Tests for app.register() with starelements components (Registrable protocol)."""

from starhtml import star_app
from starlette.testclient import TestClient

from starelements import element, get_static_path


class TestRegisterFunction:
    """Test app.register() with starelements components."""

    def test_register_creates_static_route(self):
        """app.register() creates route for static files."""

        @element("test-elem")
        def TestElem():
            return None

        app, rt = star_app()
        app.register(TestElem)

        static_routes = [r for r in app.routes if "starelements" in r.path]
        assert len(static_routes) == 1
        assert "/_pkg/starelements/" in static_routes[0].path

    def test_register_injects_headers(self):
        """app.register() adds headers to app."""

        @element("header-test")
        def HeaderTest():
            return None

        app, rt = star_app()
        initial_hdrs = len(app.hdrs)

        app.register(HeaderTest)

        assert len(app.hdrs) > initial_hdrs

    def test_register_with_custom_prefix(self):
        """app.register() respects custom prefix."""

        @element("prefix-test")
        def PrefixTest():
            return None

        app, rt = star_app()
        app.register(PrefixTest, prefix="/custom/path")

        custom_routes = [r for r in app.routes if "/custom/path" in r.path]
        assert len(custom_routes) == 1

    def test_register_multiple_components(self):
        """app.register() handles multiple components."""

        @element("multi-a")
        def MultiA():
            return None

        @element("multi-b")
        def MultiB():
            return None

        app, rt = star_app()
        app.register(MultiA, MultiB)

        template_strs = [str(h) for h in app.hdrs]
        assert any("multi-a" in s for s in template_strs)
        assert any("multi-b" in s for s in template_strs)


class TestStaticFileServing:
    """Test static file serving through app.register()."""

    def test_serve_runtime_js(self):
        """Static route serves starelements.js."""

        @element("serve-test")
        def ServeTest():
            return None

        app, rt = star_app()
        app.register(ServeTest)
        client = TestClient(app)

        response = client.get("/_pkg/starelements/starelements.js")
        assert response.status_code == 200
        assert "text/javascript" in response.headers["content-type"]
        assert len(response.content) > 0

    def test_serve_minified_js(self):
        """Static route serves minified JS."""

        @element("minify-test")
        def MinifyTest():
            return None

        app, rt = star_app()
        app.register(MinifyTest)
        client = TestClient(app)

        response = client.get("/_pkg/starelements/starelements.min.js")
        assert response.status_code == 200
        assert "text/javascript" in response.headers["content-type"]

    def test_nonexistent_file_returns_404(self):
        """Non-existent files return 404."""

        @element("notfound-test")
        def NotFoundTest():
            return None

        app, rt = star_app()
        app.register(NotFoundTest)
        client = TestClient(app)

        response = client.get("/_pkg/starelements/nonexistent.js")
        assert response.status_code == 404


class TestSecurity:
    """Test security aspects of static file serving."""

    def test_path_traversal_blocked(self):
        """Path traversal attempts are blocked."""

        @element("security-test")
        def SecurityTest():
            return None

        app, rt = star_app()
        app.register(SecurityTest)
        client = TestClient(app)

        traversal_paths = [
            "/_pkg/starelements/../README.md",
            "/_pkg/starelements/../../pyproject.toml",
            "/_pkg/starelements/../../../etc/passwd",
        ]

        for path in traversal_paths:
            response = client.get(path)
            assert response.status_code in [403, 404], f"Path not blocked: {path}"

    def test_url_encoded_traversal_blocked(self):
        """URL-encoded path traversal is blocked."""

        @element("encoded-test")
        def EncodedTest():
            return None

        app, rt = star_app()
        app.register(EncodedTest)
        client = TestClient(app)

        response = client.get("/_pkg/starelements/..%2F..%2FREADME.md")
        assert response.status_code in [403, 404]

    def test_directory_listing_blocked(self):
        """Directory listing returns 404."""

        @element("dir-test")
        def DirTest():
            return None

        app, rt = star_app()
        app.register(DirTest)
        client = TestClient(app)

        response = client.get("/_pkg/starelements/")
        assert response.status_code == 404

    def test_symlink_outside_directory_blocked(self):
        """Symlinks pointing outside static dir are blocked."""
        import os
        import tempfile
        from pathlib import Path

        @element("symlink-test")
        def SymlinkTest():
            return None

        static_path = get_static_path()
        temp_file = Path(tempfile.gettempdir()) / "sensitive.txt"
        temp_file.write_text("Sensitive")
        symlink_path = static_path / "test_symlink.txt"

        try:
            os.symlink(temp_file, symlink_path)

            app, rt = star_app()
            app.register(SymlinkTest)
            client = TestClient(app)

            response = client.get("/_pkg/starelements/test_symlink.txt")
            assert response.status_code in [403, 404]

        finally:
            symlink_path.unlink(missing_ok=True)
            temp_file.unlink(missing_ok=True)


class TestCustomPrefix:
    """Test custom prefix functionality."""

    def test_custom_prefix_works(self):
        """Files accessible via custom prefix (starhtml appends package name)."""

        @element("custom-prefix-test")
        def CustomPrefixTest():
            return None

        app, rt = star_app()
        app.register(CustomPrefixTest, prefix="/assets/libs")
        client = TestClient(app)

        # starhtml builds full_prefix = f"{prefix}/{package_name}"
        response = client.get("/assets/libs/starelements/starelements.js")
        assert response.status_code == 200

    def test_old_prefix_not_accessible(self):
        """Default prefix doesn't work with custom prefix."""

        @element("old-prefix-test")
        def OldPrefixTest():
            return None

        app, rt = star_app()
        app.register(OldPrefixTest, prefix="/new/path")
        client = TestClient(app)

        response = client.get("/_pkg/starelements/starelements.js")
        assert response.status_code == 404


class TestHeaderInjection:
    """Test header injection functionality."""

    def test_style_header_injected(self):
        """Style header is injected."""

        @element("style-test", dimensions={"min_height": "200px"})
        def StyleTest():
            return None

        app, rt = star_app()
        app.register(StyleTest)

        style_strs = [str(h) for h in app.hdrs if "<style>" in str(h).lower()]
        assert len(style_strs) > 0

        combined = "".join(style_strs)
        assert "style-test" in combined

    def test_script_header_injected(self):
        """Script header with correct src is injected."""

        @element("script-test")
        def ScriptTest():
            return None

        app, rt = star_app()
        app.register(ScriptTest)

        script_strs = [str(h) for h in app.hdrs if "<script" in str(h).lower()]
        assert len(script_strs) > 0

        combined = "".join(script_strs)
        assert "starelements.min.js" in combined

    def test_template_header_injected(self):
        """Template header is injected."""

        @element("template-test")
        def TemplateTest():
            return None

        app, rt = star_app()
        app.register(TemplateTest)

        template_strs = [str(h) for h in app.hdrs if "data-star:template-test" in str(h)]
        assert len(template_strs) == 1

    def test_skeleton_css_injected(self):
        """Skeleton CSS is injected when skeleton=True."""

        @element("skeleton-test", dimensions={"min_height": "300px"}, skeleton=True)
        def SkeletonTest():
            return None

        app, rt = star_app()
        app.register(SkeletonTest)

        style_strs = [str(h) for h in app.hdrs if "<style>" in str(h).lower()]
        combined = "".join(style_strs)
        assert "star-shimmer" in combined or "@keyframes" in combined
