"""Base Emulator class for Appium automation.

Provides core functionality for Android device/emulator control via Appium.
"""

import subprocess
import socket
import time
import re
import logging
import pytesseract
from typing import Optional
from PIL import Image

from appium.webdriver.appium_service import AppiumService
from appium.webdriver.extensions.action_helpers import ActionBuilder, PointerInput, interaction, ActionChains
from appium.options.common import AppiumOptions
from appium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from ..adb import connect_adb, get_device_info
from ..utils import load_config, LOG_FILE


logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
    encoding='utf-8'
)

CONFIG = load_config()


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def get_element_rect(element):
    """Return (x, y, w, h) tuple for a given element."""
    try:
        rect = element.rect
        return int(rect["x"]), int(rect["y"]), int(rect["width"]), int(rect["height"])
    except Exception:
        bounds = element.get_attribute("bounds")
        nums = list(map(int, re.findall(r"\d+", bounds)))
        x, y, right, bottom = nums
        w, h = right - x, bottom - y
        return x, y, w, h


def crop_element_to_file(element, screenshot_path: str = "screen.png", crop_path: str = "crop.png") -> str:
    """Crop element from screenshot and save to file."""
    screenshot = Image.open(screenshot_path)
    x, y, w, h = get_element_rect(element)
    cropped = screenshot.crop((x, y, x + w, y + h))
    cropped.save(crop_path)
    return crop_path


def ocr_from_element(element: "webdriver.WebElement", screenshot_path: str = "screen.png") -> str:
    """Extract text from element using OCR."""
    crop_path = crop_element_to_file(element, screenshot_path)
    img = Image.open(crop_path)
    return pytesseract.image_to_string(img)


def get_screenshot(driver: webdriver.Remote, path: str = "screen.png") -> str:
    """Take screenshot and save to file."""
    driver.get_screenshot_as_file(path)
    return path


# ---------------------------------------------------------------------------
# Base Emulator class
# ---------------------------------------------------------------------------

class Emulator:
    """Base class for Android emulator/device automation via Appium."""

    ADB_PATH = r"C:\Android\platform-tools\adb.exe"

    def __init__(self, udid=None, appium_port=4723, emulator_path=None, emulator_name=None, physical_device=False):
        self.udid = udid
        self.appium_port = appium_port
        self.emulator_path = emulator_path
        self.emulator_name = emulator_name
        self.driver: webdriver = None
        self.appium_service = None
        self.is_physical = None

        if physical_device:
            self.udid = input("Input UDID of your physical device: ")
        else:
            if self.udid and not connect_adb(self.udid):
                logging.error(f"Failed to connect to ADB for {self.udid}")
                raise RuntimeError(f"Failed to connect to ADB for {self.udid}")

            process = subprocess.Popen(
                f'"{self.ADB_PATH}" devices',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True
            )
            output, error = process.communicate()
            if error:
                logging.error(f"Error listing devices: {error.decode()}")
                raise RuntimeError(f"Error listing devices: {error.decode()}")
            logging.info(f"Connected devices: {output.decode()}")

        if self.udid:
            get_device_info(self.udid)

        if not self._is_port_free(appium_port):
            logging.error(f"Appium port {appium_port} is already in use")
            raise RuntimeError(f"Appium port {appium_port} is already in use")

        self.appium_service = AppiumService()
        try:
            self.appium_service.start(args=['--address', '127.0.0.1', '--port', str(appium_port)])
            logging.info(f"Appium service started on port {appium_port}")
            time.sleep(10)
        except Exception as e:
            logging.error(f"Failed to start Appium service: {e}")
            raise RuntimeError(f"Failed to start Appium service: {e}")

    @staticmethod
    def _is_port_free(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('127.0.0.1', port)) != 0

    @staticmethod
    def get_emulator_udid():
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
        devices = [line.split('\t')[0] for line in result.stdout.splitlines() if '\tdevice' in line]
        return devices[0] if devices else None

    def is_emulator_running(self):
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
        return self.udid in result.stdout and 'device' in result.stdout if self.udid else False

    def start_emulator(self, app_path, app_name):
        if not self.is_emulator_running():
            logging.info(f"Starting emulator: {app_path}")
            subprocess.Popen(app_path, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(30)
            self.udid = self.get_emulator_udid()
            if not self.udid:
                logging.error("Failed to get emulator UDID after starting")
                raise RuntimeError("Failed to get emulator UDID after starting")
        else:
            logging.info("Emulator is already running")

    def start_appium(self):
        self.appium_service.start(args=['--address', '127.0.0.1', '--port', str(self.appium_port)])
        logging.info(f"Appium service started on port {self.appium_port}")

    def start_driver(self, app_package: str, app_activity: str, no_reset=True):
        try:
            options = AppiumOptions()
            options.load_capabilities({
                "platformName": "Android",
                "deviceName": self.udid if self.udid else "Android Emulator",
                "appium:udid": self.udid,
                "appium:platformVersion": "10",
                "appium:appPackage": app_package,
                "appium:appActivity": app_activity,
                "appium:noReset": no_reset,
                "appium:autoGrantPermissions": True,
                "appium:newCommandTimeout": 120,
                "appium:automationName": "UiAutomator2",
                "appium:unicodeKeyboard": True,
                "appium:resetKeyboard": True,
            })
            self.driver = webdriver.Remote(f"http://127.0.0.1:{self.appium_port}", options=options)
            logging.info(f"WebDriver created for {self.udid}")
        except Exception as e:
            logging.error(f"Failed to create WebDriver: {e}")
            raise RuntimeError(f"Failed to create WebDriver: {e}")

    # ----------------------------- Element helpers -----------------------------

    def check_element(self, by, value, timeout=30):
        wait = WebDriverWait(self.driver, timeout)
        try:
            return wait.until(EC.presence_of_element_located((by, value)))
        except (TimeoutException, NoSuchElementException):
            logging.error(f"Элемент {value} не появился за {timeout} секунд")
            return False

    def wait_for_element_to_disappear(self, by, value, timeout=10):
        wait = WebDriverWait(self.driver, timeout)
        try:
            return wait.until(EC.invisibility_of_element_located((by, value)))
        except (TimeoutException, NoSuchElementException):
            logging.error(f"Элемент {value} не исчез за {timeout} секунд")
            return False

    def check_element_present(self, by1, value1, by2, value2, timeout=5):
        wait = WebDriverWait(self.driver, timeout)
        try:
            wait.until(EC.presence_of_element_located((by1, value1)))
            return "element1"
        except (TimeoutException, NoSuchElementException):
            pass
        try:
            wait.until(EC.presence_of_element_located((by2, value2)))
            return "element2"
        except (TimeoutException, NoSuchElementException):
            return None

    def click_element(self, by, value, timeout=10):
        wait = WebDriverWait(self.driver, timeout)
        try:
            element = wait.until(EC.element_to_be_clickable((by, value)))
            element.click()
        except (TimeoutException, NoSuchElementException) as e:
            logging.error(f"Не удалось найти или кликнуть элемент {value}: {e}")
            raise

    def clear_text_field(self, by, value, timeout=10):
        wait = WebDriverWait(self.driver, timeout)
        try:
            field = wait.until(EC.presence_of_element_located((by, value)))
            field.clear()
        except (TimeoutException, NoSuchElementException) as e:
            logging.error(f"Не удалось найти поле ввода {value}: {e}")
            raise

    def send_keys(self, by, value, text, timeout=10):
        wait = WebDriverWait(self.driver, timeout)
        try:
            field = wait.until(EC.presence_of_element_located((by, value)))
            field.clear()
            field.send_keys(text)
        except (TimeoutException, NoSuchElementException) as e:
            logging.error(f"Не удалось найти поле ввода {value}: {e}")
            raise

    def get_element_text(self, by, value, timeout=10):
        wait = WebDriverWait(self.driver, timeout)
        try:
            element = wait.until(EC.presence_of_element_located((by, value)))
            return element.text
        except (TimeoutException, NoSuchElementException) as e:
            logging.error(f"Не удалось найти элемент {value}: {e}")
            raise

    # ----------------------------- Scroll helpers -----------------------------

    def scroll(self, start_x, start_y, end_x, end_y, duration=1000):
        actions = ActionChains(self.driver)
        actions.w3c_actions = ActionBuilder(
            self.driver,
            mouse=PointerInput(interaction.POINTER_TOUCH, "touch")
        )
        actions.w3c_actions.pointer_action.move_to_location(start_x, start_y)
        actions.w3c_actions.pointer_action.pointer_down()
        actions.w3c_actions.pointer_action.pause(duration / 1000.0)
        actions.w3c_actions.pointer_action.move_to_location(end_x, end_y)
        actions.w3c_actions.pointer_action.pointer_up()
        actions.perform()

    def scroll_element(self, element, direction="up", amount=0.5):
        rect = element.rect
        start_x = rect['x'] + rect['width'] // 2
        start_y = rect['y'] + rect['height'] // 2
        if direction == "up":
            end_y = start_y - int(rect['height'] * amount)
        else:
            end_y = start_y + int(rect['height'] * amount)
        self.scroll(start_x, start_y, start_x, end_y)

    def scroll_until_element_visible(
        self,
        scrollable_area: str,
        element_to_find: str,
        max_scrolls: int = 10
    ) -> Optional["webdriver.WebElement"]:
        """Scroll until element becomes visible."""
        for _ in range(max_scrolls):
            try:
                element = self.driver.find_element(By.XPATH, element_to_find)
                if element.is_displayed():
                    return element
            except NoSuchElementException:
                pass
            scrollable = self.driver.find_element(By.XPATH, scrollable_area)
            rect = scrollable.rect
            start_x = rect["x"] + rect["width"] // 2
            start_y = rect["y"] + int(rect["height"] * 0.8)
            end_y = rect["y"] + int(rect["height"] * 0.2)
            self.scroll(start_x, start_y, start_x, end_y)
        return None

    def scroll_container_until_xpath(
        self,
        container_path: str,
        element_xpath: str,
        max_scrolls: int = 10,
        scroll_ratio: float = 0.7,
        sleep_between: float = 0.5
    ):
        """Scroll container until element is found."""
        try:
            container = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, container_path))
            )
        except Exception as e:
            raise Exception(f"Failed to locate scrollable container at {container_path}: {str(e)}")

        for _ in range(max_scrolls):
            try:
                element = container.find_element(By.XPATH, element_xpath)
                if element.is_displayed():
                    logging.info(f"Element found within container: {element_xpath}")
                    return element
            except NoSuchElementException:
                pass

            rect = container.rect
            start_x = rect["x"] + rect["width"] // 2
            start_y = rect["y"] + int(rect["height"] * 0.8)
            end_y = rect["y"] + int(rect["height"] * (1.0 - scroll_ratio))

            try:
                actions = ActionChains(self.driver)
                actions.w3c_actions = ActionBuilder(
                    self.driver,
                    mouse=PointerInput(interaction.POINTER_TOUCH, "touch")
                )
                actions.w3c_actions.pointer_action.move_to_location(start_x, start_y)
                actions.w3c_actions.pointer_action.pointer_down()
                actions.w3c_actions.pointer_action.pause(0.3)
                actions.w3c_actions.pointer_action.move_to_location(start_x, end_y)
                actions.w3c_actions.pointer_action.pointer_up()
                actions.perform()
                time.sleep(sleep_between)
            except Exception as e:
                raise Exception(f"Failed to scroll container at {container_path}: {str(e)}")

        logging.warning(f"Element not found within container after {max_scrolls} scrolls: {element_xpath}")
        return None

    def double_click_element(self, by, element_path: str) -> None:
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((by, element_path))
            )
            rect = element.rect
            x = rect['x'] + rect['width'] // 2
            y = rect['y'] + rect['height'] // 2
            self.driver.execute_script("mobile: doubleClickGesture", {"x": x, "y": y})
        except Exception as e:
            raise Exception(f"Failed to double click element at {element_path}: {str(e)}")

    # ----------------------------- Lifecycle -----------------------------

    def close(self):
        if self.appium_service is not None:
            try:
                self.appium_service.stop()
                logging.info("Appium service stopped")
            except Exception as e:
                logging.error(f"Error stopping Appium service: {e}")

        if self.driver is not None:
            try:
                self.driver.quit()
                logging.info("WebDriver closed")
            except Exception as e:
                logging.error(f"Error closing WebDriver: {e}")
