"""starelements - Web components for StarHTML/Datastar."""

from .decorator import element
from .integration import get_static_path
from .signals import Local

__all__ = [
    "element",
    "get_static_path",
    "Local",
]
__version__ = "0.1.0"
