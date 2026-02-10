"""Tests for starelements core definitions."""

import pytest

from starelements.core import ElementDef


class TestElementDef:
    def test_valid_tag_name(self):
        """Element tag must contain hyphen."""
        elem = ElementDef(tag_name="my-component")
        assert elem.tag_name == "my-component"

    def test_invalid_tag_name_raises(self):
        """Tag without hyphen should raise ValueError."""
        with pytest.raises(ValueError, match="must contain hyphen"):
            ElementDef(tag_name="mycomponent")

    def test_defaults(self):
        """ElementDef has sensible defaults."""
        elem = ElementDef(tag_name="test-elem")
        assert elem.imports == {}
        assert elem.events == []
        assert elem.render_fn is None
        assert elem.shadow is False
        assert elem.form_associated is False
