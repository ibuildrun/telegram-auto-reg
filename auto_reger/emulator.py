import subprocess
import socket
import time
import re
import random
import logging
import pytesseract
import os
from typing import Literal, Tuple, List, Callable, Optional, Union
from PIL import Image
from .adb import connect_adb, get_device_info
from appium.webdriver.appium_service import AppiumService
from appium.webdriver.extensions.action_helpers import ActionBuilder, PointerInput, interaction, ActionChains
from .utils import load_config, read_json, LOG_FILE
from appium.options.common import AppiumOptions
from appium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException


# Logging configuration
logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
    encoding='utf-8'
)
CONFIG = load_config()


def get_element_rect(element):
    """
    Return (x, y, w, h) tuple for a given element.

    Uses element.rect if available, otherwise falls back to the 'bounds'
    attribute provided by Android UI elements.
    """
    try:
        rect = element.rect
        return int(rect["x"]), int(rect["y"]), int(rect["width"]), int(rect["height"])
    except Exception:
        bounds = element.get_attribute("bounds")  # "[left,top][right,bottom]"
        nums = list(map(int, re.findall(r"\d+", bounds)))
        x, y, right, bottom = nums
        w, h = right - x, bottom - y
        return x, y, w, h


def crop_element_to_file(element, screenshot_path: str = "screen.png", crop_path: str = "crop.png") -> str:
    screenshot = Image.open(screenshot_path)

    x, y, w, h = get_element_rect(element)

    cropped = screenshot.crop((x, y, x + w, y + h))
    cropped.save(crop_path)
    return crop_path


def ocr_from_element(element: "webdriver.WebElement", screenshot_path: str = "screen.png") -> str:
    crop_path = crop_element_to_file(element, screenshot_path)
    img = Image.open(crop_path)
    return pytesseract.image_to_string(img)


def get_screenshot(driver: webdriver.Remote, path: str = "screen.png") -> str:
    driver.get_screenshot_as_file(path)
    return path


class Emulator:
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
            # Проверка подключения ADB, если UDID уже известен
            if self.udid and not connect_adb(self.udid):
                logging.error(f"Failed to connect to ADB for {self.udid}")
                raise RuntimeError(f"Failed to connect to ADB for {self.udid}")

            # Вывод списка устройств
            process = subprocess.Popen(f'"{self.ADB_PATH}" devices', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            output, error = process.communicate()
            if error:
                logging.error(f"Error listing devices: {error.decode()}")
                raise RuntimeError(f"Error listing devices: {error.decode()}")
            logging.info(f"Connected devices: {output.decode()}")

        # Информация об устройстве, если UDID известен
        if self.udid:
            get_device_info(self.udid)

        # Проверка, свободен ли порт Appium
        if not self._is_port_free(appium_port):
            logging.error(f"Appium port {appium_port} is already in use")
            raise RuntimeError(f"Appium port {appium_port} is already in use")

        # Запуск Appium-сервера
        self.appium_service = AppiumService()
        try:
            self.appium_service.start(args=['--address', '127.0.0.1', '--port', str(appium_port)])
            logging.info(f"Appium service started on port {appium_port}")
            import time
            time.sleep(10)  # Добавляем задержку
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
            process = subprocess.Popen(app_path, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(30)  # Ожидание загрузки эмулятора
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

            self.driver: webdriver = webdriver.Remote(f"http://127.0.0.1:{self.appium_port}", options=options)
            logging.info(f"WebDriver created for {self.udid}")
        except Exception as e:
            logging.error(f"Failed to create WebDriver: {e}")
            raise RuntimeError(f"Failed to create WebDriver: {e}")

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
            end_x = start_x
            end_y = start_y - int(rect['height'] * amount)
        else:
            end_x = start_x
            end_y = start_y + int(rect['height'] * amount)

        self.scroll(start_x, start_y, end_x, end_y)

    def scroll_until_element_visible(
        self,
        scrollable_area: str,
        element_to_find: str,
        max_scrolls: int = 10
    ) -> Optional["webdriver.WebElement"]:
        """
        Scrolls vertically inside the scrollable_area until element_to_find becomes visible or max_scrolls is reached.
        """
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
        """Scrolls a scrollable container until element matching element_xpath is found or max_scrolls is reached."""
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

            self.driver.execute_script(
                "mobile: doubleClickGesture",
                {"x": x, "y": y}
            )
        except Exception as e:
            raise Exception(f"Failed to double click element at {element_path}: {str(e)}")

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


class Telegram(Emulator):
    START_MESSENGER = '//android.widget.TextView[@text="Start Messaging"]'
    PHONE_NUMBER_INPUT = '//android.widget.EditText[@text="Your phone number"]'
    COUNTRY_CODE_INPUT = '//android.widget.EditText[@resource-id="org.telegram.messenger:id/country_code"]'
    DONE_BTN = '//android.widget.TextView[@text="Done"]'
    YES_BTN = '//android.widget.TextView[@text="Yes"]'
    CONTINUE_BTN = '//android.widget.TextView[@text="Continue"]'
    ALLOW_BTN = '//android.widget.Button[@text="Allow"]'
    ALLOW_CALLING_MESSAGE = '//android.widget.TextView[@text="Allow Telegram to make and manage phone calls?"]'
    ALLOW_CALLING_LIST_MESSAGE = '//android.widget.TextView[@text="Allow Telegram to access your contacts?"]'
    MENU_BTN = '//android.widget.ImageView[@content-desc="Open navigation menu"]'
    SETTINGS_BTN = '(//android.widget.TextView[@text="Settings"])[1]/android.view.View'
    MORE_OPTIONS = '//android.widget.ImageButton[@content-desc="More options"]/android.widget.ImageView'
    LOG_OUT_OPTIONS = '//android.widget.TextView[@text="Log Out"]'
    LOG_OUT_BTN = '(//android.widget.TextView[@text="Log Out"])[2]'
    CHAT_WITH_TELEGRAM = '//android.view.ViewGroup'
    NUMBER_IS_BANNED = '//android.widget.TextView[@text="This phone number is banned."]'
    OK_BTN = '//android.widget.TextView[@text="OK"]'
    PASS_NEED_TEXT = '//android.widget.TextView[@text="Two-Step Verification is enabled. Your account is protected with an additional password."]'
    FORGOT_PASS_BTN = '//android.widget.TextView[@text="Forgot password?"]'
    RESET_ACC_BTN = '//android.widget.TextView[@text="Reset account"]'
    CHECK_EMAIL_TEXT = '//android.widget.TextView[@text="Check Your Email"]'
    TOO_MANY_ATTEMPTS = '//android.widget.TextView[@text="Too many attempts, please try again later."]'
    ENTER_CODE_TEXT = '//android.widget.TextView[@text="Enter code"]'
    MESSAGES_BOX = '//androidx.recyclerview.widget.RecyclerView'
    ACCEPT_BTN = '//android.widget.TextView[@text="Accept"]'
    GET_CODE_VIA_SMS = '//android.widget.TextView[@text="Get the code via SMS"]'
    TELEGRAM_ADB_NAME = 'org.telegram.messenger'
    GO_BACK_BTN = '//android.widget.ImageView[@content-desc="Go back"]'
    PRIVACY_AND_SECURITY_BTN = '//android.widget.TextView[@text="Privacy and Security"]'
    TWO_STEP_VERIF_BTN = '//android.widget.TextView[@text="Two-Step Verification"]'
    SET_PASSWORD_BTN = '//android.widget.TextView[@text="Set Password"]'
    ENTER_PASSWORD_FIELD = '//android.widget.EditText[@content-desc="Enter password"]'
    NEXT_BTN = '//android.widget.FrameLayout[@content-desc="Next"]'
    REENTER_PASSWORD_FIELD = '//android.widget.EditText[@content-desc="Re-enter password"]'
    HINT_FIELD = '//android.widget.EditText[@content-desc="Hint"]'
    SKIP_BTN = '//android.widget.TextView[@text="Skip"]'
    RETURN_TO_SETTINGS_BTN = '//android.widget.TextView[@text="Return to Settings"]'
    SET_PROFILE_PHOTO_BTN = '//android.widget.TextView[@text="Set Profile Photo"]'
    PHOTO_LAST = 'new UiSelector().className("android.view.View").instance(1)'
    PHOTO_NEW = '(//android.widget.LinearLayout[@resource-id="org.telegram.messenger:id/cell_layout"])[1]'
    USERNAME_FIELD = '//android.widget.EditText[@resource-id="org.telegram.messenger:id/first_name_field"]'
    USERNAME_FIELD_NEW = '//android.widget.EditText[@resource-id="org.telegram.messenger:id/username"]'
    SELF_CHAT = '//android.widget.TextView[@text="Saved Messages"]'
    AUDIO_PERMISSION = '(//android.widget.Button[@resource-id="com.android.permissioncontroller:id/permission_allow_button"])[2]'
    CAMERA_PERMISSION = '(//android.widget.Button[@resource-id="com.android.permissioncontroller:id/permission_allow_button"])[1]'
    CAMERA_PERMISSION_2 = '(//android.widget.Button[@resource-id="com.android.permissioncontroller:id/permission_allow_foreground_only_button"])[1]'
    MICROPHONE_PERMISSION = '(//android.widget.Button[@resource-id="com.android.permissioncontroller:id/permission_allow_button"])[3]'
    STORAGE_PERMISSION = '//android.widget.Button[@resource-id="com.android.permissioncontroller:id/permission_allow_button"]'
    PHOTO_UPLOAD_FROM_GALLERY = '//android.widget.TextView[@resource-id="org.telegram.messenger:id/photos_btn"]'
    PHOTO_GALLERY_FOLDER = '//android.widget.TextView[@text="Download"]'
    PHOTO_FROM_GALLERY = '(//android.widget.ImageView[@resource-id="org.telegram.messenger:id/thumb"])[1]'
    MENU_BTN_SETTINGS = '(//android.widget.TextView[@text="Settings"])[2]'
    SEARCH_BTN = '//android.widget.ImageView[@content-desc="Search"]'
    SEARCH_FIELD = '//android.widget.EditText[@resource-id="org.telegram.messenger:id/search_src_text"]'
    CHATS_LIST = '//android.widget.ListView[@resource-id="org.telegram.messenger:id/chat_list_view"]'
    CHAT = '(//android.widget.LinearLayout[@resource-id="org.telegram.messenger:id/chat_list_row"])[1]'
    CHAT_NAME = '//android.widget.TextView[@resource-id="org.telegram.messenger:id/action_bar_title"]'
    MESSAGE_FIELD = '//android.widget.EditText[@resource-id="org.telegram.messenger:id/chat_edit_text"]'
    SEND_BTN = '//android.widget.ImageButton[@resource-id="org.telegram.messenger:id/chat_send_button"]'
    REACTION_BTN = '(//android.widget.FrameLayout[@resource-id="org.telegram.messenger:id/reactions_layout"])[1]'
    REACTION_LIST = '//androidx.recyclerview.widget.RecyclerView[@resource-id="org.telegram.messenger:id/emoji_list"]'
    REACTION_ITEM = '(//android.widget.LinearLayout[@resource-id="org.telegram.messenger:id/cell"])[1]'
    JOIN_BTN = '//android.widget.TextView[@text="Join"]'
    LEAVE_CHANNEL_BTN = '//android.widget.TextView[@text="Leave channel"]'
    LEAVE_CHANNEL_OK_BTN = '//android.widget.Button[@text="Leave"]'

    REGISTRATION_NAME_FIELD = '//android.widget.EditText[@resource-id="org.telegram.messenger:id/first_name_field"]'
    REGISTRATION_SURNAME_FIELD = '//android.widget.EditText[@resource-id="org.telegram.messenger:id/last_name_field"]'
    REGISTRATION_DONE_BTN = '//android.widget.FrameLayout[@resource-id="org.telegram.messenger:id/next_button"]'
    AGREE_BTN = '//android.widget.TextView[@resource-id="org.telegram.messenger:id/positive_button"]'
    CONNECT = '//android.widget.TextView[@text="Connecting..."]'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_driver(app_package=self.TELEGRAM_ADB_NAME, app_activity=".ui.LaunchActivity")

    def start_messenger(self):
        if self.check_element(By.XPATH, self.START_MESSENGER, timeout=10):
            self.click_element(By.XPATH, self.START_MESSENGER)
        else:
            logging.info("Start Messaging button not found, maybe already started")

    def input_phone_number(self, number):
        self.start_messenger()
        wait = WebDriverWait(self.driver, 10)

        try:
            phone_number_field = wait.until(EC.presence_of_element_located((By.XPATH, self.PHONE_NUMBER_INPUT)))
        except (TimeoutException, NoSuchElementException):
            logging.error("Элемент для ввода номера не найден")
            return
        phone_number_field.clear()

        self.send_keys(By.XPATH, self.COUNTRY_CODE_INPUT, number)
        self.click_element(By.XPATH, self.DONE_BTN)
        self.click_element(By.XPATH, self.YES_BTN, timeout=3)

        if self.check_element(By.XPATH, self.CONTINUE_BTN, timeout=2):
            self.click_element(By.XPATH, self.CONTINUE_BTN)

        if self.check_element(By.XPATH, '//android.widget.Button[@resource-id="com.android.packageinstaller:id/permission_allow_button"]', timeout=2):
            self.click_element(By.XPATH, '//android.widget.Button[@resource-id="com.android.packageinstaller:id/permission_allow_button"]')

    def click_continue_second_windows(self, timeout=2):
        try:
            self.click_element(By.XPATH, self.CONTINUE_BTN, timeout)
        except (TimeoutException, NoSuchElementException):
            pass

    def click_allow_btn(self, timeout=2):
        if self.check_element(By.XPATH, self.ALLOW_CALLING_MESSAGE, timeout):
            self.click_element(By.XPATH, self.ALLOW_BTN)

        if self.check_element(By.XPATH, self.ALLOW_CALLING_LIST_MESSAGE, timeout):
            self.click_element(By.XPATH, self.ALLOW_BTN)

    def check_banned(self):
        return self.check_element(By.XPATH, self.NUMBER_IS_BANNED, timeout=5)

    def click_ok_btn(self):
        self.click_element(By.XPATH, self.OK_BTN)

    def check_pass_need(self):
        return self.check_element(By.XPATH, self.PASS_NEED_TEXT, timeout=5)

    def click_forgot_pass_btn(self):
        self.click_element(By.XPATH, self.FORGOT_PASS_BTN)

    def click_reset_acc_btn(self):
        self.click_element(By.XPATH, self.RESET_ACC_BTN)

    def check_check_email(self):
        return self.check_element(By.XPATH, self.CHECK_EMAIL_TEXT, timeout=5)

    def check_too_many_attempts(self):
        return self.check_element(By.XPATH, self.TOO_MANY_ATTEMPTS, timeout=5)

    def check_enter_code_text(self):
        return self.check_element(By.XPATH, self.ENTER_CODE_TEXT, timeout=5)

    def click_accept_btn(self):
        self.click_element(By.XPATH, self.ACCEPT_BTN)

    def click_get_code_via_sms(self):
        self.click_element(By.XPATH, self.GET_CODE_VIA_SMS)

    def open_settings(self):
        self.click_element(By.XPATH, self.MENU_BTN)
        self.click_element(By.XPATH, self.SETTINGS_BTN)

    def log_out(self):
        self.open_settings()
        self.click_element(By.XPATH, self.MORE_OPTIONS)
        self.click_element(By.XPATH, self.LOG_OUT_OPTIONS)
        self.click_element(By.XPATH, self.LOG_OUT_BTN)

    def set_2fa_password(self, password, hint=""):
        self.open_settings()
        self.click_element(By.XPATH, self.PRIVACY_AND_SECURITY_BTN)
        self.click_element(By.XPATH, self.TWO_STEP_VERIF_BTN)
        self.click_element(By.XPATH, self.SET_PASSWORD_BTN)

        self.send_keys(By.XPATH, self.ENTER_PASSWORD_FIELD, password)
        self.click_element(By.XPATH, self.NEXT_BTN)
        self.send_keys(By.XPATH, self.REENTER_PASSWORD_FIELD, password)
        self.click_element(By.XPATH, self.NEXT_BTN)
        self.send_keys(By.XPATH, self.HINT_FIELD, hint)
        self.click_element(By.XPATH, self.NEXT_BTN)
        self.click_element(By.XPATH, self.SKIP_BTN)
        self.click_element(By.XPATH, self.RETURN_TO_SETTINGS_BTN)

    def set_profile_photo_from_gallery(self):
        self.open_settings()
        self.click_element(By.XPATH, self.SET_PROFILE_PHOTO_BTN)

        if self.check_element(By.XPATH, self.AUDIO_PERMISSION, timeout=2):
            self.click_element(By.XPATH, self.AUDIO_PERMISSION)
        if self.check_element(By.XPATH, self.CAMERA_PERMISSION, timeout=2):
            self.click_element(By.XPATH, self.CAMERA_PERMISSION)
        if self.check_element(By.XPATH, self.CAMERA_PERMISSION_2, timeout=2):
            self.click_element(By.XPATH, self.CAMERA_PERMISSION_2)
        if self.check_element(By.XPATH, self.MICROPHONE_PERMISSION, timeout=2):
            self.click_element(By.XPATH, self.MICROPHONE_PERMISSION)
        if self.check_element(By.XPATH, self.STORAGE_PERMISSION, timeout=2):
            self.click_element(By.XPATH, self.STORAGE_PERMISSION)

        self.click_element(By.XPATH, self.PHOTO_UPLOAD_FROM_GALLERY)
        self.click_element(By.XPATH, self.PHOTO_GALLERY_FOLDER)
        self.click_element(By.XPATH, self.PHOTO_FROM_GALLERY)

    def set_username(self, username):
        self.open_settings()
        self.click_element(By.XPATH, self.USERNAME_FIELD)
        self.clear_text_field(By.XPATH, self.USERNAME_FIELD_NEW)
        self.send_keys(By.XPATH, self.USERNAME_FIELD_NEW, username)
        self.click_element(By.XPATH, self.NEXT_BTN)

    def go_to_self_chat(self):
        self.click_element(By.XPATH, self.SELF_CHAT)

    def send_message_to_self(self, message):
        self.go_to_self_chat()
        self.send_keys(By.XPATH, self.MESSAGE_FIELD, message)
        self.click_element(By.XPATH, self.SEND_BTN)

    def search_chat(self, chat_name):
        self.click_element(By.XPATH, self.SEARCH_BTN)
        self.send_keys(By.XPATH, self.SEARCH_FIELD, chat_name)

    def open_first_chat(self):
        self.click_element(By.XPATH, self.CHAT)

    def get_chat_name(self):
        return self.get_element_text(By.XPATH, self.CHAT_NAME)

    def send_message(self, message):
        self.send_keys(By.XPATH, self.MESSAGE_FIELD, message)
        self.click_element(By.XPATH, self.SEND_BTN)

    def react_to_message(self):
        self.click_element(By.XPATH, self.REACTION_BTN)
        self.click_element(By.XPATH, self.REACTION_ITEM)

    def join_channel(self):
        if self.check_element(By.XPATH, self.JOIN_BTN, timeout=5):
            self.click_element(By.XPATH, self.JOIN_BTN)

    def leave_channel(self):
        self.click_element(By.XPATH, self.MORE_OPTIONS)
        self.click_element(By.XPATH, self.LEAVE_CHANNEL_BTN)
        self.click_element(By.XPATH, self.LEAVE_CHANNEL_OK_BTN)

    def registration_name_and_surname(self, name, surname):
        """
        Вводит имя и фамилию во время регистрации.
        """
        self.send_keys(By.XPATH, self.REGISTRATION_NAME_FIELD, name)
        self.send_keys(By.XPATH, self.REGISTRATION_SURNAME_FIELD, surname)
        self.click_element(By.XPATH, self.REGISTRATION_DONE_BTN)
        self.click_element(By.XPATH, self.AGREE_BTN)

    def check_connect_status(self):
        """
        Проверяет статус 'Connecting...'.
        """
        return self.check_element(By.XPATH, self.CONNECT, timeout=5)

    def read_sms_with_code(self, timeout=120):
        telegram_chat = '//android.view.ViewGroup'
        message_xpath = '//android.view.ViewGroup[contains(@text, "Login code: ")]'

        recycler_view_xpath = "//androidx.recyclerview.widget.RecyclerView"
        WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, recycler_view_xpath))
        )
        logging.info("RecyclerView найден")

        # Получение всех ViewGroup элементов в RecyclerView
        chat_elements = self.driver.find_elements(By.XPATH, f"{recycler_view_xpath}/android.view.ViewGroup")
        logging.info(f"Найдено {len(chat_elements)} элементов чата")

        code = None

        for chat in chat_elements:
            try:
                # Проверяем, содержит ли чат сообщение "Login code: "
                chat_text = chat.text
                logging.info(f"Текст чата: {chat_text}")

                if "Login code: " in chat_text:
                    logging.info("Найдено сообщение с Login code.")
                    # Извлекаем код из текста сообщения
                    match = re.search(r"Login code: (\d+)", chat_text)
                    if match:
                        code = match.group(1)
                        logging.info(f"Извлечён код: {code}")
                        break
            except Exception as e:
                logging.error(f"Ошибка при обработке чата: {e}")

        if code is None:
            logging.warning("Код не найден в сообщениях")
        else:
            logging.info(f"Код успешно найден: {code}")

        return code


class Instagram(Emulator):
    INSTAGRAM_LITE_ADB_NAME = 'com.instagram.lite'
    INSTAGRAM_LITE_ACTIVITY = 'com.instagram.mainactivity.MainActivity'

    SIGN_UP_EMAIL_BTN = '//android.widget.TextView[@text="Sign up with email or phone number"]'
    EMAIL_OPTION_BTN = '//android.widget.TextView[@text="Email"]'
    EMAIL_FIELD = '//android.widget.EditText[@resource-id="com.instagram.lite:id/email_field"]'
    NEXT_BTN = '//android.widget.TextView[@text="Next"]'
    CONFIRM_EMAIL_BTN = '//android.widget.TextView[@text="Confirm"]'
    FULL_NAME_FIELD = '//android.widget.EditText[@resource-id="com.instagram.lite:id/full_name"]'
    PASSWORD_FIELD = '//android.widget.EditText[@resource-id="com.instagram.lite:id/password"]'
    BIRTHDAY_FIELD = '//android.widget.EditText[@resource-id="com.instagram.lite:id/birthday"]'
    SIGN_UP_BTN = '//android.widget.Button[@resource-id="com.instagram.lite:id/sign_up"]'
    SAVE_LOGIN_INFO_BTN = '//android.widget.Button[@resource-id="com.instagram.lite:id/primary_button"]'
    TURN_ON_NOTIFICATIONS_BTN = '//android.widget.Button[@resource-id="com.instagram.lite:id/turn_on"]'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_driver(app_package=self.INSTAGRAM_LITE_ADB_NAME, app_activity=self.INSTAGRAM_LITE_ACTIVITY)

    def sign_up_with_email(self, email, full_name, password, birthday):
        self.click_element(By.XPATH, self.SIGN_UP_EMAIL_BTN)
        self.click_element(By.XPATH, self.EMAIL_OPTION_BTN)
        self.send_keys(By.XPATH, self.EMAIL_FIELD, email)
        self.click_element(By.XPATH, self.NEXT_BTN)

        self.send_keys(By.XPATH, self.FULL_NAME_FIELD, full_name)
        self.send_keys(By.XPATH, self.PASSWORD_FIELD, password)
        self.send_keys(By.XPATH, self.BIRTHDAY_FIELD, birthday)
        self.click_element(By.XPATH, self.SIGN_UP_BTN)

        if self.check_element(By.XPATH, self.SAVE_LOGIN_INFO_BTN, timeout=5):
            self.click_element(By.XPATH, self.SAVE_LOGIN_INFO_BTN)

        if self.check_element(By.XPATH, self.TURN_ON_NOTIFICATIONS_BTN, timeout=5):
            self.click_element(By.XPATH, self.TURN_ON_NOTIFICATIONS_BTN)
