"""Telegram Desktop automation.

Provides automation for Telegram Desktop client on Windows.
"""

import logging
import os
import time

from pywinauto.findwindows import ElementNotFoundError

from .base import App, maximize_window
from ..utils import LOG_FILE


logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s",
    encoding="utf-8",
)


class TelegramDesktop(App):
    """
    Automation wrapper for Telegram Desktop client on Windows.

    Used for:
      * Entering a phone number.
      * Typing the login code received via SMS.
    """

    def __init__(self, app_path: str) -> None:
        super().__init__()
        self.app = self.start_app(app_path=app_path)
        self.app_name = os.path.basename(app_path)
        self.window = None

    def start_and_enter_number(self, phone_number: str) -> bool:
        """
        Open Telegram Desktop window and enter phone number into login form.

        :param phone_number: Phone number in international format.
        :return: True on success, False on error.
        """
        try:
            self.window = self.app.window(title="Telegram")
            self.window.wait("ready", timeout=30)

            maximize_window(self.window.handle)
            self.window.set_focus()
            time.sleep(2)
            logging.info("Telegram window found and maximized")

            # Click "Start Messaging" / "Log in" if present
            try:
                start_btn = self.window.child_window(
                    title_re=".*Start Messaging.*|.*Log in.*",
                    control_type="Button",
                )
                if start_btn.exists():
                    start_btn.click_input()
                    logging.info("Start/Login button clicked")
                    time.sleep(2)
            except ElementNotFoundError:
                logging.info("Start/Login button not found — maybe already on phone screen")

            # Try to find input field by control type/position
            number_input_field = None
            try:
                number_input_field = self.window.child_window(
                    control_type="Edit",
                    found_index=0,
                )
            except ElementNotFoundError:
                pass

            if not number_input_field:
                # Fallback: use legacy coordinates heuristic
                number_input_field = self.get_element_by_position(
                    self.window, "Edit", 772, 550, 1147, 600
                )

            if not number_input_field:
                logging.error("Phone number input field not found")
                return False

            number_input_field.set_text("")
            number_input_field.type_keys(phone_number, with_spaces=True)
            logging.info("Phone number typed")

            # "Next" button heuristic: by position or title
            try:
                next_btn = self.window.child_window(
                    title_re=".*Next.*", control_type="Button"
                )
                if next_btn.exists():
                    next_btn.click_input()
                    logging.info("Next button clicked")
                    return True
            except ElementNotFoundError:
                pass

            next_btn = self.get_element_by_position(
                self.window, "Group", 772, 608, 1147, 660
            )
            if next_btn:
                next_btn.click_input()
                logging.info("SMS request sent (Next button clicked via position)")
                return True

            logging.error("Next button not found")
            return False

        except ElementNotFoundError as e:
            logging.error("ElementNotFoundError during start_and_enter_number: %s", e)
            if self.window:
                self.window.print_control_identifiers()
            return False
        except NotImplementedError as e:
            logging.error("NotImplementedError during start_and_enter_number: %s", e)
            return False
        except Exception as e:
            logging.error("General error during start_and_enter_number: %s", e)
            if self.window:
                self.window.print_control_identifiers()
            return False

    def enter_code(self, code: str) -> bool:
        """
        Enter received login code into Telegram Desktop login form.

        :param code: Login code as string.
        :return: True on success, False on error.
        """
        try:
            if not self.window:
                self.window = self.app.window(title="Telegram")
                self.window.wait("ready", timeout=30)

            self.window.set_focus()
            time.sleep(1)

            code_field = self.window.child_window(
                control_type="Edit", found_index=0
            )
            code_field.wait("visible", timeout=20)
            code_field.set_text("")
            code_field.type_keys(code, with_spaces=False)
            logging.info("Login code entered into Telegram Desktop")
            return True

        except ElementNotFoundError as e:
            logging.error("ElementNotFoundError during enter_code: %s", e)
            if self.window:
                self.window.print_control_identifiers()
            return False
        except NotImplementedError as e:
            logging.error("NotImplementedError during enter_code: %s", e)
            return False
        except Exception as e:
            logging.error("General error during enter_code: %s", e)
            if self.window:
                self.window.print_control_identifiers()
            return False
