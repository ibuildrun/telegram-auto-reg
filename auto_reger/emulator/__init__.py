"""Emulator automation package.

Provides Appium-based automation for Android emulators and devices.
"""

from .base import Emulator, get_element_rect, crop_element_to_file, ocr_from_element, get_screenshot
from .telegram import Telegram
from .instagram import Instagram

__all__ = [
    "Emulator",
    "Telegram",
    "Instagram",
    "get_element_rect",
    "crop_element_to_file",
    "ocr_from_element",
    "get_screenshot",
]
