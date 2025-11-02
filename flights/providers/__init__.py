__all__ = [
    "BaseProvider",
    "easyjet",
    "providers",
]

from . import easyjet
from .base import BaseProvider

providers: list[type[BaseProvider]] = [
    easyjet.EasyJet,
]
