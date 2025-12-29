"""ExpressVPN automation.

Provides automation for ExpressVPN desktop application.
"""

import logging
import random
import time

from pywinauto.findwindows import ElementNotFoundError

from .base import App
from ..utils import LOG_FILE


logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s",
    encoding="utf-8",
)


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
