__all__ = [
    "BaseProvider",
    "easyjet",
    "tap",
    "providers",
]

from . import easyjet
from . import tap
from .base import BaseProvider

providers: list[type[BaseProvider]] = [
    easyjet.EasyJet,
    tap.TAP,
]
