"""Onion Mail automation via Google Chrome.

Provides automation for Onion Mail web UI running in Chrome browser.
"""

import logging
import re
import time
from typing import Literal, Optional

import pyautogui
from pywinauto.findwindows import ElementNotFoundError

from .base import App
from ..utils import LOG_FILE


logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s",
    encoding="utf-8",
)


class Onion(App):
    """
    Automation wrapper for Onion Mail web UI (running in Google Chrome).

    Used for:
      * Registering new mailbox.
      * Logging in with existing mailbox.
      * Extracting confirmation codes from inbox (Telegram / Instagram).
    """

    def __init__(self) -> None:
        super().__init__()
        self.app = self.start_app("onion")
        self.window = None

    def _is_capcha_window_present(self, timeout: int = 5) -> bool:
        """Check whether a reCAPTCHA/anti-bot Chrome window is present."""
        end_time = time.time() + timeout
        while time.time() < end_time:
            try:
                window = self.app.window(title_re="Один момент.*Google Chrome.*")
                if window.exists():
                    return True
            except Exception:
                pass
            time.sleep(1)
        return False

    def capcha_hack(self) -> bool:
        """
        Attempt to automatically pass the "I'm not a robot" checkbox.

        This logic is highly environment-specific and may require manual
        adjustments (coordinates, language, etc.).
        """
        try:
            window = self.app.window(title_re="Один момент.*Google Chrome.*")
            window.wait("visible", timeout=20)
            window.set_focus()

            start_time = time.time()
            while time.time() - start_time < 300:
                if not window.exists():
                    logging.info("Captcha window disappeared during waiting")
                    return False

                try:
                    checkbox = window.child_window(
                        title="Подтвердите, что вы человек",
                        control_type="CheckBox",
                    )
                    if checkbox.exists() and checkbox.is_visible():
                        try:
                            checkbox.click_input()
                            logging.info("Captcha checkbox clicked via UIA")
                            return True
                        except Exception:
                            rect = checkbox.rectangle()
                            x = rect.left + rect.width() // 2
                            y = rect.top + rect.height() // 2
                            pyautogui.moveTo(x, y, duration=0.5)
                            pyautogui.click()
                            logging.info("Captcha checkbox clicked via pyautogui")
                            return True

                except ElementNotFoundError:
                    pass

                time.sleep(3)

            logging.warning("Captcha window did not show a checkbox in time")
            return False
        except Exception as e:
            logging.error("Error during captcha hack: %s", e)
            return False

    def reg_and_login(
        self, username: str, password: str, domain: Optional[str] = None
    ) -> Optional[str]:
        """
        Register a new Onion Mail account and log in with it.

        :param username: Desired username (without domain).
        :param password: Password for the mailbox.
        :param domain: Optional custom domain (e.g. "onionmail.org").
        :return: Full email address on success, None on failure.
        """
        email: Optional[str] = None

        try:
            self.window = self.app.window(title_re="Onion Mail.*Google Chrome.*")
            self.window.wait("ready", timeout=20)
            self.window.set_focus()
            logging.info("Found Chrome window with Onion Mail tab")

            # If already logged in (INBOX visible) → log out first
            try:
                is_inbox_txt = self.window.child_window(
                    title=" INBOX", control_type="Text", found_index=0
                ).exists(timeout=1)
            except ElementNotFoundError:
                is_inbox_txt = False

            if is_inbox_txt:
                buttons = self.window.descendants(control_type="Button")
                target_btn = None
                for btn in buttons:
                    rect = btn.rectangle()
                    if rect.top == 108 and rect.right == 1682 and rect.bottom == 172:
                        target_btn = btn
                        break
                if target_btn:
                    target_btn.click_input()
                    logging.info("Main menu activated")

                try:
                    log_out = self.window.child_window(
                        control_type="Hyperlink", title="Log out", found_index=0
                    )
                    log_out.wait("visible", timeout=3)
                except Exception:
                    log_out = self.window.child_window(
                        control_type="Hyperlink", title=" Log out", found_index=0
                    )
                    log_out.wait("visible", timeout=3)
                log_out.invoke()
                logging.info("Successfully logged out from previous account")

            # Open "Create account" form
            create_acc_btn = self.window.child_window(
                title=" Create account",
                control_type="Hyperlink",
                found_index=0,
            )
            create_acc_btn.wait("visible", timeout=10)
            create_acc_btn.invoke()
            logging.info("Create account form opened")

            # Handle captcha if it appears
            if self._is_capcha_window_present(timeout=10):
                logging.info("Captcha window detected, starting capcha_hack()")
                if self.capcha_hack():
                    logging.info("Captcha passed")
                else:
                    logging.error("Captcha hack failed")
            else:
                logging.info("Captcha window not detected, continuing")

            # Domain selection
            if domain:
                domain_menu = self.window.child_window(
                    control_type="Button", title="@onionmail.org", found_index=0
                )
                domain_menu.wait("visible", timeout=30)
                domain_menu.click_input()

                domain_item = self.window.child_window(
                    control_type="Hyperlink", title=domain, found_index=0
                )
                domain_item.wait("visible", timeout=10)
                domain_item.click_input()
                email = f"{username}@{domain}"
            else:
                email = f"{username}@onionmail.org"

            # Fill registration fields
            name_field = self.window.child_window(
                control_type="Edit", auto_id="name", found_index=0
            )
            name_field.wait("ready", timeout=60)
            time.sleep(1)
            name_field.set_text("")
            name_field.type_keys(username, with_spaces=True)
            logging.info("Name entered")

            username_field = self.window.child_window(
                control_type="Edit", auto_id="username", found_index=0
            )
            username_field.wait("ready", timeout=60)
            username_field.set_text("")
            username_field.type_keys(username, with_spaces=True)
            logging.info("Username entered")

            password_field = self.window.child_window(
                control_type="Edit", auto_id="password", found_index=0
            )
            password_field.wait("ready", timeout=60)
            password_field.set_text("")
            password_field.type_keys(password, with_spaces=True)
            logging.info("Password entered")

            repeat_password_field = self.window.child_window(
                control_type="Edit", auto_id="repassword", found_index=0
            )
            repeat_password_field.wait("ready", timeout=60)
            repeat_password_field.set_text("")
            repeat_password_field.type_keys(password, with_spaces=True)
            logging.info("Password repeated")

            # Checkbox: "I agree to the Terms..."
            agree_checkbox = self.window.child_window(
                control_type="CheckBox", auto_id="terms", found_index=0
            )
            agree_checkbox.wait("ready", timeout=10)
            if not agree_checkbox.is_checked():
                agree_checkbox.click_input()
            logging.info("Terms checkbox checked")

            # Submit registration
            create_account_btn = self.window.child_window(
                control_type="Button", title="CREATE NEW ACCOUNT", found_index=0
            )
            create_account_btn.wait("visible", timeout=10)
            create_account_btn.invoke()
            logging.info("New mailbox created")
            time.sleep(5)

            # Log in with new credentials
            try:
                is_login_txt = self.window.child_window(
                    title=" Log in", control_type="Text", found_index=0
                ).exists(timeout=10)
            except ElementNotFoundError:
                is_login_txt = False

            if is_login_txt:
                username_field_log = self.window.child_window(
                    control_type="Edit", auto_id="username", found_index=0
                )
                username_field_log.wait("visible", timeout=60)
                username_field_log.set_text("")
                username_field_log.type_keys(username, with_spaces=True)
                logging.info("Login username entered")

                password_field_log = self.window.child_window(
                    control_type="Edit", auto_id="password", found_index=0
                )
                password_field_log.wait("visible", timeout=60)
                password_field_log.set_text("")
                password_field_log.type_keys(password, with_spaces=True)
                logging.info("Login password entered")

                try:
                    login_btn = self.window.child_window(
                        control_type="Button", title=" LOG IN"
                    )
                    login_btn.wait("visible", timeout=1)
                except Exception:
                    login_btn = self.window.child_window(
                        control_type="Button", title="LOG IN"
                    )
                    login_btn.wait("visible", timeout=1)

                login_btn.click_input()
                logging.info("Logged into newly created mailbox")

            return email

        except ElementNotFoundError as e:
            logging.error("ElementNotFoundError during reg_and_login: %s", e)
            if self.window:
                self.window.print_control_identifiers()
            return None
        except Exception as e:
            logging.error("General error during reg_and_login: %s", e)
            if self.window:
                self.window.print_control_identifiers()
            return None

    def extract_code(
        self,
        service: Literal["telegram", "instagram"],
        time_out: int = 5,
        second_req: bool = False,
    ) -> str:
        """
        Extract numeric confirmation code for the given service from inbox.

        :param service: "telegram" or "instagram".
        :param time_out: Wait timeout for each UI operation.
        :param second_req: For Telegram, optionally use alternative subject.
        :return: Code as string, or empty string if not found.
        """
        attempts = 3
        attempt = 0
        code_text = ""

        try:
            self.window = self.app.window(title_re="Onion Mail.*Google Chrome.*")
            self.window.wait("visible", timeout=20)
            self.window.set_focus()

            while attempt < attempts:
                attempt += 1

                # Reload inbox
                try:
                    reload_page = self.window.child_window(
                        title="Перезагрузить",
                        control_type="Button",
                        found_index=0,
                    )
                    reload_page.wait("visible", timeout=time_out)
                    reload_page.invoke()
                    logging.info("Inbox reloaded (attempt %s)", attempt)
                except ElementNotFoundError:
                    logging.warning("Reload button not found on attempt %s", attempt)

                time.sleep(3)

                try:
                    if service == "telegram":
                        subjects = [
                            "Telegram",
                            "Telegram code",
                            "Login code",
                        ]
                        if second_req:
                            subjects.insert(0, "Telegram (second request)")

                        msg = None
                        for subj in subjects:
                            try:
                                msg = self.window.child_window(
                                    title_re=f".*{re.escape(subj)}.*",
                                    control_type="Text",
                                )
                                if msg.exists():
                                    break
                            except ElementNotFoundError:
                                continue
                    else:  # instagram
                        msg = self.window.child_window(
                            title_re=".*Instagram.*",
                            control_type="Text",
                        )

                    if msg and msg.exists():
                        text = msg.window_text()
                        m = re.search(r"(\d{5,6})", text)
                        if m:
                            code_text = m.group(1)
                            logging.info(
                                "Found %s code in inbox on attempt %s: %s",
                                service,
                                attempt,
                                code_text,
                            )
                            break
                except ElementNotFoundError:
                    logging.info("Service message not found on attempt %s", attempt)

            return code_text

        except Exception as e:
            logging.error("Error while extracting %s code: %s", service, e)
            if self.window:
                self.window.print_control_identifiers()
            return ""
