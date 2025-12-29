"""Base class and helpers for Windows desktop automation.

Provides common functionality for automating Windows GUI applications
using pywinauto.
"""

import logging
import os
import time
from typing import Optional

import psutil
import win32con
import win32gui
from pywinauto import Application, findwindows

from ..utils import LOG_FILE


logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s",
    encoding="utf-8",
)


def maximize_window(window_handle: int) -> None:
    """Maximize a top-level window using Win32 API."""
    win32gui.ShowWindow(window_handle, win32con.SW_MAXIMIZE)


def get_handle(app_title_regex: str) -> Optional[int]:
    """
    Find first top-level window whose title matches the given regex.

    :param app_title_regex: Regex for window title.
    :return: Window handle (HWND) or None if not found.
    """
    try:
        handles = findwindows.find_windows(title_re=app_title_regex)
        if handles:
            return handles[0]
        return None
    except findwindows.ElementNotFoundError:
        return None


class App:
    """
    Base helper for automating Windows desktop applications using pywinauto.

    Responsibilities:
      * Start or attach to a running app.
      * Find main window using a title regex.
      * Gracefully close main window and kill background processes.
    """

    def __init__(self) -> None:
        self.handle_title: Optional[str] = None
        self.app_name: Optional[str] = None
        self.app: Optional[Application] = None

    def start_app(
        self,
        app_name: Optional[str] = None,
        app_path: Optional[str] = None,
        backend: str = "uia",
    ) -> Application:
        """
        Start (or attach to) a Windows application.

        Known presets:
          * app_name='onion' → Google Chrome with Onion Mail tab.
          * app_name='vpn'   → ExpressVPN UI.
          * app_path containing 'Telegram.exe' → Telegram Desktop.

        :param app_name: Logical app name used by this project.
        :param app_path: Full path to executable (if not using preset).
        :param backend: pywinauto backend, usually 'uia'.
        :return: Connected pywinauto.Application instance.
        """
        app = Application(backend=backend)

        if not app_name and not app_path:
            raise ValueError("You must specify either app_name or app_path")

        # Preset configuration
        if app_name == "onion":
            self.handle_title = ".*Google Chrome.*"
            app_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            self.app_name = os.path.basename(app_path)

        elif app_name == "vpn":
            self.handle_title = "ExpressVPN.*"
            app_path = r"C:\Program Files (x86)\ExpressVPN\expressvpn-ui\ExpressVPN.exe"
            self.app_name = os.path.basename(app_path)

        # Telegram Desktop by explicit path
        if app_path and "Telegram.exe" in app_path:
            self.handle_title = "Telegram"
            self.app_name = os.path.basename(app_path)

        if not self.handle_title:
            raise ValueError("handle_title is not set; unknown app preset")

        # Try to attach to existing instance first
        handle = get_handle(self.handle_title)
        if handle:
            logging.info("Attaching to existing window: %s (handle=%s)", self.handle_title, handle)
            app.connect(handle=handle)
        else:
            # Start a new instance
            logging.info("Starting application: %s", app_path)
            app.start(app_path or self.app_name)
            # Wait for main window to appear
            handle = None
            timeout = time.time() + 60
            while time.time() < timeout:
                handle = get_handle(self.handle_title)
                if handle:
                    break
                time.sleep(1)
            if not handle:
                raise RuntimeError(f"Failed to find window with title {self.handle_title!r} after launch")

        self.app = app
        return app

    @staticmethod
    def get_element_by_position(window, control_type: str, left: int, top: int, right: int, bottom: int):
        """
        Find first descendant element of given control_type by absolute bounds.

        This is brittle and depends on exact DPI/layout.
        """
        elements = window.descendants(control_type=control_type)
        for elem in elements:
            rect = elem.rectangle()
            if rect.left == left and rect.top == top and rect.right == right and rect.bottom == bottom:
                return elem
        return None

    def close(self) -> None:
        """Close main window and kill remaining background processes."""
        if not self.handle_title:
            logging.warning("close() called without handle_title configured")
            return

        try:
            app = Application(backend="uia").connect(title_re=self.handle_title)
            app.window(title_re=self.handle_title).close()
            logging.info("Main window %s closed", self.handle_title)
        except Exception as e:
            logging.warning("Failed to close main window %s: %s", self.handle_title, e)

        # Kill background processes by name
        if self.app_name:
            for proc in psutil.process_iter(["name"]):
                try:
                    if proc.info["name"] == self.app_name:
                        logging.info("Killing background process: %s", proc.info["name"])
                        proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
