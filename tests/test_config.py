"""Tests for pyproject.toml config parsing."""


class TestBundleConfig:
    def test_bundle_config_fields(self):
        """BundleConfig has required fields."""
        from starelements.bundler.config import BundleConfig

        config = BundleConfig(
            packages=["peaks.js@3", "konva@9"],
            minify=True,
        )

        assert config.packages == ["peaks.js@3", "konva@9"]
        assert config.minify is True

    def test_bundle_config_defaults(self):
        """BundleConfig has sensible defaults."""
        from starelements.bundler.config import BundleConfig

        config = BundleConfig(packages=["test@1"])

        assert config.minify is True  # default

    def test_bundles_dir_constant(self):
        """BUNDLES_DIR is the expected convention path."""
        from starelements.bundler.config import BUNDLES_DIR

        assert BUNDLES_DIR == ".starelements/bundles"


class TestLoadConfig:
    def test_load_config_parses_toml(self, tmp_path):
        """load_config parses [tool.starelements] section."""
        from starelements.bundler.config import load_config

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[project]
name = "test-project"

[tool.starelements]
bundle = ["peaks.js@3", "konva@9"]
""")

        config = load_config(tmp_path)

        assert config is not None
        assert config.packages == ["peaks.js@3", "konva@9"]
        assert config.minify is True  # default

    def test_load_config_minify_false(self, tmp_path):
        """load_config respects minify=false."""
        from starelements.bundler.config import load_config

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.starelements]
bundle = ["test@1"]
minify = false
""")

        config = load_config(tmp_path)

        assert config.minify is False

    def test_load_config_no_pyproject(self, tmp_path):
        """load_config returns None when no pyproject.toml."""
        from starelements.bundler.config import load_config

        config = load_config(tmp_path)

        assert config is None

    def test_load_config_no_starelements_section(self, tmp_path):
        """load_config returns None when no [tool.starelements]."""
        from starelements.bundler.config import load_config

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[project]
name = "test-project"

[tool.pytest]
testpaths = ["tests"]
""")

        config = load_config(tmp_path)

        assert config is None

    def test_load_config_no_bundle_key(self, tmp_path):
        """load_config returns None when no bundle key."""
        from starelements.bundler.config import load_config

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.starelements]
minify = false
""")

        config = load_config(tmp_path)

        assert config is None
