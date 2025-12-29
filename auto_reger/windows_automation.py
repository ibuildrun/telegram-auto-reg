import logging
import os
import random
import re
import time
from typing import Literal, Optional

import psutil
import pyautogui
import win32con
import win32gui
from pywinauto import Application, findwindows
from pywinauto.findwindows import ElementNotFoundError
from selenium.common.exceptions import NoSuchElementException

from .utils import LOG_FILE


logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s",
    encoding="utf-8",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def maximize_window(window_handle: int) -> None:
    """
    Maximize a top-level window using Win32 API.
    """
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


# ---------------------------------------------------------------------------
# Base class for Windows GUI apps
# ---------------------------------------------------------------------------

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

    # ---------------------------- core lifecycle ----------------------------

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
            # NOTE: this path is environment-specific, adjust if needed
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

    # ---------------------------- small helpers -----------------------------

    @staticmethod
    def get_element_by_position(window, control_type: str, left: int, top: int, right: int, bottom: int):
        """
        Find first descendant element of given control_type by absolute bounds.

        This is very brittle and depends on exact DPI/layout, but kept for
        compatibility with the original project.
        """
        elements = window.descendants(control_type=control_type)
        for elem in elements:
            rect = elem.rectangle()
            if rect.left == left and rect.top == top and rect.right == right and rect.bottom == bottom:
                return elem
        return None

    # ----------------------------- shutdown ---------------------------------

    def close(self) -> None:
        """
        Close main window and kill remaining background processes.

        This uses both pywinauto (for main window) and psutil (for lingering
        processes with the same executable name).
        """
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


# ---------------------------------------------------------------------------
# Onion Mail via Google Chrome
# ---------------------------------------------------------------------------

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

    # ---------------------------- captcha helpers ---------------------------

    def _is_capcha_window_present(self, timeout: int = 5) -> bool:
        """
        Check whether a reCAPTCHA/anti-bot Chrome window is present.

        Looks for a separate Chrome window with title "Один момент..." which
        appears when Google performs additional checks.
        """
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
        adjustments (coordinates, language, etc.). The idea:

          * Wait for the Chrome window "Один момент...".
          * Wait for the "Подтвердите, что вы человек" checkbox.
          * Use pyautogui to move and click the checkbox if visible.
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
                        # Try to click via pywinauto first
                        try:
                            checkbox.click_input()
                            logging.info("Captcha checkbox clicked via UIA")
                            return True
                        except Exception:
                            # Fallback: approximate center using pyautogui
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

    # -------------------------- registration / login ------------------------

    def reg_and_login(self, username: str, password: str, domain: Optional[str] = None) -> Optional[str]:
        """
        Register a new Onion Mail account and log in with it.

        The method:
          * Attaches to 'Onion Mail' Chrome tab.
          * If currently logged in (INBOX visible), logs out.
          * Opens "Create account" form.
          * Solves captcha if needed.
          * Fills name / username / password fields.
          * Submits the form.
          * Logs in using new credentials.

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
                    # These coordinates are from the original project and may
                    # need tuning depending on DPI/layout.
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

    # ------------------------------- inbox ----------------------------------

    def extract_code(
        self,
        service: Literal["telegram", "instagram"],
        time_out: int = 5,
        second_req: bool = False,
    ) -> str:
        """
        Extract numeric confirmation code for the given service from inbox.

        This is a best-effort implementation based on the original logic:

          * Open Onion Mail tab in Chrome.
          * Click "Reload" button several times.
          * Locate the latest message related to the given service.
          * Extract the first 5–6 digit number from message preview.

        :param service: "telegram" or "instagram".
        :param time_out: Wait timeout for each UI operation.
        :param second_req: For Telegram, optionally use alternative subject
                           text for a second request.
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

                # Try to locate message element depending on service
                try:
                    if service == "telegram":
                        # Different subjects may be used; we try several variants
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


# ---------------------------------------------------------------------------
# ExpressVPN automation
# ---------------------------------------------------------------------------

class VPN(App):
    """
    Automation wrapper for ExpressVPN desktop app.

    Used for:
      * Disconnecting/connecting VPN.
      * Changing location (country).
    """

    def __init__(self, backend: str = "uia") -> None:
        super().__init__()
        self.app = self.start_app("vpn", backend=backend)
        self.window = None

    def reconnection(self) -> bool:
        """
        Disconnect and reconnect VPN on ExpressVPN main window.

        :return: True on success, False on error.
        """
        try:
            window = self.app.window(title_re="ExpressVPN.*")
            window.wait("visible", timeout=20)
            window.set_focus()
            logging.info("Found ExpressVPN window")

            disconnect_btn = window.child_window(
                title_re=r"Отключиться от.*", control_type="Button"
            )
            disconnect_btn.invoke()
            logging.info("Disconnecting from VPN...")
            time.sleep(5)

            connect_btn = window.child_window(
                title_re=r"Подключиться к.*", control_type="Button"
            )
            connect_btn.wait("visible", timeout=60)
            connect_btn.invoke()
            logging.info("Reconnecting to VPN...")
            time.sleep(10)

            logging.info("IP successfully changed via reconnection")
            return True

        except ElementNotFoundError as e:
            logging.error("ElementNotFoundError during VPN reconnection: %s", e)
            window.print_control_identifiers()
            return False
        except NotImplementedError as e:
            logging.error("NotImplementedError during VPN reconnection: %s", e)
            return False
        except Exception as e:
            logging.error("General error during VPN reconnection: %s", e)
            window.print_control_identifiers()
            return False

    def change_location(self, country: str) -> bool:
        """
        Change VPN location to a random server in the given country.

        The original logic relied on the location tree inside ExpressVPN UI:

          * Click "Choose another location".
          * Enumerate nodes in the Tree control.
          * Pick a random entry whose text starts with `<country> -`.
          * Click it.

        :param country: Country name (e.g. "United States", "Canada").
        :return: True if a location was changed, False otherwise.
        """
        try:
            window = self.app.window(title_re="ExpressVPN.*")
            window.wait("visible", timeout=20)
            window.set_focus()
            logging.info("Found ExpressVPN window")

            change_location_btn = window.child_window(
                title="Выбрать другую локацию", control_type="Button"
            )
            change_location_btn.invoke()
            time.sleep(2)

            usa_window = window.child_window(control_type="Window").child_window(
                control_type="Tree"
            )
            btns_with_location = usa_window.descendants(control_type="TreeItem")[1:]

            if btns_with_location:
                while True:
                    random_button = random.choice(btns_with_location)
                    text = random_button.texts()[0]
                    if f"{country} -" not in text:
                        continue
                    random_button.click_input()
                    logging.info("Location changed to: %s", text)
                    break
                return True

            logging.info("No matching location buttons found for country %s", country)
            return False

        except ElementNotFoundError as e:
            logging.error("ElementNotFoundError during change_location: %s", e)
            window.print_control_identifiers()
            return False
        except NotImplementedError as e:
            logging.error("NotImplementedError during change_location: %s", e)
            return False
        except Exception as e:
            logging.error("General error during change_location: %s", e)
            window.print_control_identifiers()
            return False


# ---------------------------------------------------------------------------
# Telegram Desktop automation
# ---------------------------------------------------------------------------

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

        This relies on the standard login screen layout and may require
        adjustments for localized UI or future Telegram updates.

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

            # Typical login flow:
            #  1. Click "Start Messaging" / "Log in"
            #  2. Type phone number
            #  3. Click "Next"
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
                # Many builds use a single Edit field for the number
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

            # Usually Telegram has a single Edit field for the login code.
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
