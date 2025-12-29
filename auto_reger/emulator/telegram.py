"""Telegram Android app automation.

Provides UI automation for Telegram Messenger on Android via Appium.
"""

import re
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .base import Emulator


class Telegram(Emulator):
    """Telegram Android app automation via Appium."""

    # XPath locators
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
    NUMBER_IS_BANNED = '//android.widget.TextView[@text="This phone number is banned."]'
    OK_BTN = '//android.widget.TextView[@text="OK"]'
    PASS_NEED_TEXT = '//android.widget.TextView[@text="Two-Step Verification is enabled. Your account is protected with an additional password."]'
    FORGOT_PASS_BTN = '//android.widget.TextView[@text="Forgot password?"]'
    RESET_ACC_BTN = '//android.widget.TextView[@text="Reset account"]'
    CHECK_EMAIL_TEXT = '//android.widget.TextView[@text="Check Your Email"]'
    TOO_MANY_ATTEMPTS = '//android.widget.TextView[@text="Too many attempts, please try again later."]'
    ENTER_CODE_TEXT = '//android.widget.TextView[@text="Enter code"]'
    ACCEPT_BTN = '//android.widget.TextView[@text="Accept"]'
    GET_CODE_VIA_SMS = '//android.widget.TextView[@text="Get the code via SMS"]'
    GO_BACK_BTN = '//android.widget.ImageView[@content-desc="Go back"]'

    # Privacy & Security
    PRIVACY_AND_SECURITY_BTN = '//android.widget.TextView[@text="Privacy and Security"]'
    TWO_STEP_VERIF_BTN = '//android.widget.TextView[@text="Two-Step Verification"]'
    SET_PASSWORD_BTN = '//android.widget.TextView[@text="Set Password"]'
    ENTER_PASSWORD_FIELD = '//android.widget.EditText[@content-desc="Enter password"]'
    NEXT_BTN = '//android.widget.FrameLayout[@content-desc="Next"]'
    REENTER_PASSWORD_FIELD = '//android.widget.EditText[@content-desc="Re-enter password"]'
    HINT_FIELD = '//android.widget.EditText[@content-desc="Hint"]'
    SKIP_BTN = '//android.widget.TextView[@text="Skip"]'
    RETURN_TO_SETTINGS_BTN = '//android.widget.TextView[@text="Return to Settings"]'

    # Profile
    SET_PROFILE_PHOTO_BTN = '//android.widget.TextView[@text="Set Profile Photo"]'
    USERNAME_FIELD = '//android.widget.EditText[@resource-id="org.telegram.messenger:id/first_name_field"]'
    USERNAME_FIELD_NEW = '//android.widget.EditText[@resource-id="org.telegram.messenger:id/username"]'
    SELF_CHAT = '//android.widget.TextView[@text="Saved Messages"]'

    # Permissions
    AUDIO_PERMISSION = '(//android.widget.Button[@resource-id="com.android.permissioncontroller:id/permission_allow_button"])[2]'
    CAMERA_PERMISSION = '(//android.widget.Button[@resource-id="com.android.permissioncontroller:id/permission_allow_button"])[1]'
    CAMERA_PERMISSION_2 = '(//android.widget.Button[@resource-id="com.android.permissioncontroller:id/permission_allow_foreground_only_button"])[1]'
    MICROPHONE_PERMISSION = '(//android.widget.Button[@resource-id="com.android.permissioncontroller:id/permission_allow_button"])[3]'
    STORAGE_PERMISSION = '//android.widget.Button[@resource-id="com.android.permissioncontroller:id/permission_allow_button"]'

    # Photo upload
    PHOTO_UPLOAD_FROM_GALLERY = '//android.widget.TextView[@resource-id="org.telegram.messenger:id/photos_btn"]'
    PHOTO_GALLERY_FOLDER = '//android.widget.TextView[@text="Download"]'
    PHOTO_FROM_GALLERY = '(//android.widget.ImageView[@resource-id="org.telegram.messenger:id/thumb"])[1]'

    # Chat
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

    # Registration
    REGISTRATION_NAME_FIELD = '//android.widget.EditText[@resource-id="org.telegram.messenger:id/first_name_field"]'
    REGISTRATION_SURNAME_FIELD = '//android.widget.EditText[@resource-id="org.telegram.messenger:id/last_name_field"]'
    REGISTRATION_DONE_BTN = '//android.widget.FrameLayout[@resource-id="org.telegram.messenger:id/next_button"]'
    AGREE_BTN = '//android.widget.TextView[@resource-id="org.telegram.messenger:id/positive_button"]'
    CONNECT = '//android.widget.TextView[@text="Connecting..."]'

    TELEGRAM_ADB_NAME = 'org.telegram.messenger'
    app_prefix = 'org.telegram.messenger'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_driver(app_package=self.TELEGRAM_ADB_NAME, app_activity=".ui.LaunchActivity")

    # ----------------------------- Core actions -----------------------------

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

        permission_btn = '//android.widget.Button[@resource-id="com.android.packageinstaller:id/permission_allow_button"]'
        if self.check_element(By.XPATH, permission_btn, timeout=2):
            self.click_element(By.XPATH, permission_btn)

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

    # ----------------------------- Status checks -----------------------------

    def check_banned(self):
        return self.check_element(By.XPATH, self.NUMBER_IS_BANNED, timeout=5)

    def check_pass_need(self):
        return self.check_element(By.XPATH, self.PASS_NEED_TEXT, timeout=5)

    def check_check_email(self):
        return self.check_element(By.XPATH, self.CHECK_EMAIL_TEXT, timeout=5)

    def check_too_many_attempts(self):
        return self.check_element(By.XPATH, self.TOO_MANY_ATTEMPTS, timeout=5)

    def check_enter_code_text(self):
        return self.check_element(By.XPATH, self.ENTER_CODE_TEXT, timeout=5)

    def check_connect_status(self):
        return self.check_element(By.XPATH, self.CONNECT, timeout=5)

    # ----------------------------- Button clicks -----------------------------

    def click_ok_btn(self):
        self.click_element(By.XPATH, self.OK_BTN)

    def click_forgot_pass_btn(self):
        self.click_element(By.XPATH, self.FORGOT_PASS_BTN)

    def click_reset_acc_btn(self):
        self.click_element(By.XPATH, self.RESET_ACC_BTN)

    def click_accept_btn(self):
        self.click_element(By.XPATH, self.ACCEPT_BTN)

    def click_get_code_via_sms(self):
        self.click_element(By.XPATH, self.GET_CODE_VIA_SMS)

    # ----------------------------- Settings -----------------------------

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

    # ----------------------------- Profile -----------------------------

    def set_profile_photo_from_gallery(self):
        self.open_settings()
        self.click_element(By.XPATH, self.SET_PROFILE_PHOTO_BTN)

        for perm in [self.AUDIO_PERMISSION, self.CAMERA_PERMISSION,
                     self.CAMERA_PERMISSION_2, self.MICROPHONE_PERMISSION,
                     self.STORAGE_PERMISSION]:
            if self.check_element(By.XPATH, perm, timeout=2):
                self.click_element(By.XPATH, perm)

        self.click_element(By.XPATH, self.PHOTO_UPLOAD_FROM_GALLERY)
        self.click_element(By.XPATH, self.PHOTO_GALLERY_FOLDER)
        self.click_element(By.XPATH, self.PHOTO_FROM_GALLERY)

    def set_username(self, username):
        self.open_settings()
        self.click_element(By.XPATH, self.USERNAME_FIELD)
        self.clear_text_field(By.XPATH, self.USERNAME_FIELD_NEW)
        self.send_keys(By.XPATH, self.USERNAME_FIELD_NEW, username)
        self.click_element(By.XPATH, self.NEXT_BTN)

    # ----------------------------- Chat -----------------------------

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

    # ----------------------------- Registration -----------------------------

    def registration_name_and_surname(self, name, surname):
        self.send_keys(By.XPATH, self.REGISTRATION_NAME_FIELD, name)
        self.send_keys(By.XPATH, self.REGISTRATION_SURNAME_FIELD, surname)
        self.click_element(By.XPATH, self.REGISTRATION_DONE_BTN)
        self.click_element(By.XPATH, self.AGREE_BTN)

    def read_sms_with_code(self, timeout=120):
        recycler_view_xpath = "//androidx.recyclerview.widget.RecyclerView"
        WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, recycler_view_xpath))
        )
        logging.info("RecyclerView найден")

        chat_elements = self.driver.find_elements(By.XPATH, f"{recycler_view_xpath}/android.view.ViewGroup")
        logging.info(f"Найдено {len(chat_elements)} элементов чата")

        code = None
        for chat in chat_elements:
            try:
                chat_text = chat.text
                logging.info(f"Текст чата: {chat_text}")

                if "Login code: " in chat_text:
                    logging.info("Найдено сообщение с Login code.")
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
