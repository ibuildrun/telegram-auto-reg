"""Windows desktop automation package.

Provides pywinauto-based automation for Windows desktop applications.
"""

from .base import App, maximize_window, get_handle
from .onion import Onion
from .vpn import VPN
from .telegram_desktop import TelegramDesktop

__all__ = [
    "App",
    "Onion",
    "VPN",
    "TelegramDesktop",
    "maximize_window",
    "get_handle",
]
