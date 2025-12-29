"""Instagram Lite automation via Appium.

Provides UI automation for Instagram Lite Android app registration.
"""

from selenium.webdriver.common.by import By

from .base import Emulator


class Instagram(Emulator):
    """Appium automation for Instagram Lite Android app."""

    INSTAGRAM_LITE_ADB_NAME = "com.instagram.lite"
    INSTAGRAM_LITE_ACTIVITY = "com.instagram.mainactivity.MainActivity"

    # UI element locators
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
        self.start_driver(
            app_package=self.INSTAGRAM_LITE_ADB_NAME,
            app_activity=self.INSTAGRAM_LITE_ACTIVITY,
        )

    def sign_up_with_email(self, email: str, full_name: str, password: str, birthday: str) -> None:
        """
        Register new Instagram account using email.

        :param email: Email address for registration.
        :param full_name: Display name.
        :param password: Account password.
        :param birthday: Birthday string (format depends on app locale).
        """
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
