"""Tests for starelements core definitions."""

import pytest
from starelements.core import ElementDef, PropDef, SignalDef


class TestElementDef:
    def test_valid_tag_name(self):
        """Element tag must contain hyphen."""
        elem = ElementDef(tag_name="my-component")
        assert elem.tag_name == "my-component"

    def test_invalid_tag_name_raises(self):
        """Tag without hyphen should raise ValueError."""
        with pytest.raises(ValueError, match="must contain hyphen"):
            ElementDef(tag_name="mycomponent")


class TestPropDef:
    def test_simple_string_codec(self):
        """String prop generates correct codec."""
        prop = PropDef(name="title", type_=str, default="Hello")
        assert prop.to_codec_string() == "string|=Hello"

    def test_int_with_constraints_codec(self):
        """Int prop with min/max generates correct codec."""
        prop = PropDef(name="count", type_=int, ge=0, le=100, default=50)
        assert prop.to_codec_string() == "int|min:0|max:100|=50"

    def test_required_prop_codec(self):
        """Required prop includes required! flag."""
        prop = PropDef(name="url", type_=str, required=True)
        assert "required!" in prop.to_codec_string()

    def test_float_codec(self):
        """Float prop generates float type."""
        prop = PropDef(name="value", type_=float, default=0.0)
        assert prop.to_codec_string().startswith("float")

    def test_boolean_codec(self):
        """Boolean prop generates boolean type."""
        prop = PropDef(name="disabled", type_=bool, default=False)
        assert prop.to_codec_string() == "boolean|=false"
