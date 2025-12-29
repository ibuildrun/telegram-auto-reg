"""Telegram registration orchestration script.

This module ties together ADB/emulator control, SMS APIs,
VPN and email helpers, and Telegram Desktop/TData tools
into a single workflow for registering Telegram accounts.

The code is intentionally kept as a single script so it can
be used both as a CLI tool and as a portfolio example.
"""

import subprocess
import time
import os
import random
import logging
import shutil
import sys
from datetime import datetime
from auto_reger.adb import reset_data, get_device_info
from auto_reger.utils import read_json, write_json, load_names, get_device_config, kill_emulator, generate_random_string, \
    load_config, download_random_avatar
from auto_reger.sms_api import SmsApi, remove_activation_from_json, save_activation_to_json, can_set_status_8
from auto_reger.emulator import Telegram
from auto_reger.windows import Onion, VPN, TelegramDesktop
from auto_reger.tdesktop import get_auth_key_and_dc_id
from selenium.webdriver.common.by import By
from telethon.tl.functions.contacts import ResolveUsernameRequest
from telethon.tl.functions.messages import GetDialogsRequest
from telethon import TelegramClient
from telethon.errors import FloodWaitError, FloodError, PhoneNumberOccupiedError, SessionPasswordNeededError, \
    PhoneNumberBannedError, PhoneNumberFloodError, PhoneCodeInvalidError, PhoneCodeExpiredError, PhoneCodeEmptyError, \
    PasswordHashInvalidError
from telethon.tl.types import InputPeerEmpty

logging.basicConfig(
    filename='telegram_regger.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
    encoding='utf-8'
)

CECH_PATH = './cech.json'
SESSIONS_DIR = './sessions/converted'
COUNTRY = input('Enter country for registration Telegram account (USA, United Kingdom, etc.): ').strip()
MAX_PRICE = float(input('Enter maximum price: ').strip())
NEED_CHANGE_LOCATION = False
FOLDER_NAME_WITH_ACCOUNTS = None
CONFIG = load_config()


def setup_cech():
    """Load or initialize local registration statistics.

    Uses CECH_PATH JSON file to persist counters between runs.
    """
    if os.path.isfile(CECH_PATH):
        return read_json(CECH_PATH)
    cech_data = {}
    write_json(cech_data, CECH_PATH)
    return cech_data


def perform_neutral_actions(client):
    """Perform a few harmless Telegram API calls to mimic user activity.

    Currently fetches a small slice of dialogs which helps to
    warm up a freshly created account a bit.
    """
    try:
        # Получение списка диалогов для имитации активности
        result = client(GetDialogsRequest(
            offset_date=None,
            offset_id=0,
            offset_peer=None,
            limit=10,
            hash=0
        ))
        logging.info("Neutral action: Retrieved dialogs")
        time.sleep(random.uniform(2, 5))
    except Exception as e:
        logging.error(f"Failed neutral actions: {str(e)}")


def save_session(**kwargs):
    """Persist minimal session/metadata information about a registered account.

    The resulting structure is later used for analytics or remote upload.
    """
    today = datetime.now().strftime('%Y-%m-%d')
    session_dir = os.path.join(SESSIONS_DIR, today)
    os.makedirs(session_dir, exist_ok=True)

    session_data = {
        'phone_number': kwargs.get('phone_number'),
        'device_info': kwargs.get('device_info'),
        'number_price': kwargs.get('number_price'),
        'session_path': kwargs.get('session_path'),
        'registration_time': datetime.now().isoformat()
    }

    session_file = os.path.join(session_dir, f"{kwargs.get('phone_number')}.json")
    write_json(session_data, session_file)
    logging.info(f"Session data saved for {kwargs.get('phone_number')}")


def activation_admin(sms_obj: SmsApi,
                     last_names,
                     phone_number,
                     activation_id):
    """High-level helper to finish or cancel an SMS activation.

    It updates provider status, local tracking JSON and handles
    corner cases like too-early cancellation (status 8).
    """
    global NEED_CHANGE_LOCATION
    NEED_CHANGE_LOCATION = True if random.randint(0, 100) < 30 else False
    random_last_name = random.choice(last_names) if last_names else "Unknown"

    cech_data = setup_cech()

    cech_data['last_name'] = random_last_name
    cech_data['phone_number'] = phone_number

    try:
        if can_set_status_8(activation_id):
            sms_obj.setStatus(activation_id, 8)  # Cancel activation
            remove_activation_from_json(activation_id)
            cech_data['activation_status'] = 'canceled'
            cech_data['reason'] = 'No code received or error'
            logging.info(f"Activation {activation_id} canceled.")
        else:
            cech_data['activation_status'] = 'not_canceled'
            cech_data['reason'] = 'Too early to cancel status'
            logging.info(f"Activation {activation_id} cannot be canceled yet.")
    except Exception as e:
        cech_data['activation_status'] = 'error'
        cech_data['reason'] = str(e)
        logging.error(f"Error during activation admin for {activation_id}: {e}")

    write_json(cech_data, CECH_PATH)
    return CECH_PATH


def create_tdata_with_telegram_desktop(phone_number: str, telegram: Telegram):
    """Create Telegram Desktop TData for a given phone using Android Telegram.

    The function logs into Telegram Desktop with the number, reads the
    login code from the Android Telegram app and produces an isolated
    TData folder with Telegram.exe inside.
    """
    script_path = os.path.abspath(sys.argv[0])
    script_dir = os.path.dirname(script_path)

    tg_desk_acc_dir = os.path.join(script_dir, 'sessions', 'tg_desk', phone_number)
    os.makedirs(tg_desk_acc_dir, exist_ok=True)

    tg_app_path = os.path.join(tg_desk_acc_dir, 'Telegram.exe')

    app_data_local_low = os.path.join(os.getenv('LOCALAPPDATA'), 'Telegram Desktop')
    if os.path.exists(app_data_local_low):
        shutil.rmtree(app_data_local_low)

    shutil.copy(os.path.join(os.path.dirname(__file__), 'Telegram.exe'), tg_app_path)

    tg_desk = TelegramDesktop(tg_app_path)
    tg_desk.start_and_enter_number(phone_number)
    time.sleep(5)
    code = telegram.read_sms_with_code()
    tg_desk.enter_code(code)
    time.sleep(3)
    tg_desk.close()

    os.system(f"taskkill /F /IM Telegram.exe")
    os.remove(tg_app_path)

    return tg_desk_acc_dir


async def create_session_with_telethon(phone_number,
                                       telegram: Telegram,
                                       device_model='Desktop',
                                       system_version='Windows 10',
                                       app_version='4.0.4 x64',
                                       sys_lng_code='en',
                                       lng_code='en',
                                       api_id=8,
                                       api_hash='7245de8af52cd3a3c23c8ebf5153ecf9'):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    session_dir = os.path.join(current_dir, 'sessions', 'telethon', phone_number)
    session_path = os.path.join(session_dir, f'{phone_number}.session')
    session_tdata_dir = None

    if os.path.exists(session_path):
        logging.info(f"Session already exists for {phone_number}")
        return session_path

    try:
        os.makedirs(session_dir, exist_ok=True)
        client = TelegramClient(session=session_path, api_id=api_id, api_hash=api_hash,
                                device_model=device_model, system_version=system_version,
                                app_version=app_version, system_lang_code=sys_lng_code,
                                lang_code=lng_code)
        await client.connect()

        # Запрос кода
        await client.send_code_request(phone_number)
        time.sleep(5)
        logging.info(f"Code requested for {phone_number}")

        code = telegram.read_sms_with_code()
        if code:
            try:
                await client.sign_in(phone_number, code)
                logging.info(f"Successfully logged in via Telethon for {phone_number}")
            except PhoneCodeInvalidError:
                logging.error("Invalid SMS code entered")
            except PhoneCodeExpiredError:
                logging.error("SMS code expired")
            except PhoneCodeEmptyError:
                logging.error("SMS code was not provided")
        else:
            logging.error(f"Failed to read SMS code for {phone_number}")
            return None

        result = await client(functions.help.GetConfigRequest())
        logging.info(f"Received Telegram config: {result}")

        # Выполнение нейтральных действий
        perform_neutral_actions(client)

        tdata_folder = create_tdata_with_telegram_desktop(phone_number, telegram)
        session_tdata_dir = os.path.join(tdata_folder, 'tdata')
        logging.info(f"Tdata folder created at {tdata_folder}")

        return session_path, session_tdata_dir

    except Exception as e:
        logging.error(f"Error during Telethon session creation for {phone_number}: {e}")
        return None

    finally:
        await client.disconnect()


def phone_number_send(telegram: Telegram, sms_obj: SmsApi):
    """Reserve a phone number via SMS API and send it to the Telegram app.

    Handles pricing limits, provider errors and basic retry logic.
    Returns activation id, phone number and cost on success.
    """
    global NEED_CHANGE_LOCATION

    attempt = 0

    while attempt < 5:
        attempt += 1
        try:
            # Buy a phone number
            new_number = True
            num_data = None
            while new_number:
                max_price = None
                if 'grizzly' not in sms_obj.api_url:
                    max_price = MAX_PRICE
                num_data = sms_obj.verification_number('tg', COUNTRY, max_price)
                print(num_data)
                phone_number = num_data.get('phoneNumber')
                activation_id = num_data.get('activationId')
                number_price = num_data.get('activationCost')

                if not phone_number:
                    if num_data['error']:
                        logging.error(f"Нет номеров. Переходим к следующей попытке...")
                        continue
                    else:
                        logging.error(f"SMS API response: {num_data}")
                        return False

                # Check if country code matches the expected one
                if COUNTRY == "United Kingdom" and not phone_number.startswith('+44'):
                    logging.warning(f"Получен номер с неверным кодом. Ожидался +44, получен {phone_number}. Пытаемся еще раз...")
                    activation_admin(sms_obj, [], phone_number, activation_id)
                    continue
                elif COUNTRY == "USA" and not phone_number.startswith('+1'):
                    logging.warning(f"Получен номер с неверным кодом. Ожидался +1, получен {phone_number}. Пытаемся еще раз...")
                    activation_admin(sms_obj, [], phone_number, activation_id)
                    continue
                else:
                    new_number = False

            # Send number to Telegram
            telegram.input_phone_number(phone_number)

            # Save activation
            save_activation_to_json(activation_id, phone_number)
            logging.info(f"Activation {activation_id} saved with phone number {phone_number}")

            return activation_id, phone_number, number_price

        except Exception as e:
            logging.error(f"Error in phone_number_send attempt {attempt}: {e}")
            if attempt >= 5:
                logging.error("Maximum attempts reached in phone_number_send")
                return False


def check_2fa(telegram: Telegram):
    """Check whether the current Telegram UI flow requires 2FA password.

    Uses Appium element checks to detect password screens and banners.
    """
    if telegram.check_pass_need():
        telegram.click_forgot_pass_btn()
        time.sleep(5)

        if telegram.check_check_email():
            logging.info("Two-step verification required, check your email.")
            return True

    return False


def register_telegram_account(device_config,
                              sms_srvice,
                              sms_api_key_path,
                              first_names,
                              last_names,
                              attempt):
    """Full pipeline to register one Telegram account on a given device.

    Orchestrates device reset, VPN, SMS activation, Telegram UI automation,
    session/TData creation and basic error handling.
    Returns True on success, False otherwise.
    """
    global FOLDER_NAME_WITH_ACCOUNTS, NEED_CHANGE_LOCATION

    emulator_path = device_config['emulator_path']
    emulator_name = device_config['emulator_name']
    is_physical = device_config['is_physical']

    sms_obj = SmsApi(service=sms_srvice, api_key_path=sms_api_key_path)
    onion = Onion()

    device_info = get_device_info(device_config['udid'])
    logging.info(f"Device info: {device_info}")

    telegram = Telegram(
        udid=device_config['udid'],
        appium_port=device_config['appium_port'],
        emulator_path=emulator_path,
        emulator_name=emulator_name,
        physical_device=is_physical
    )

    try:
        logging.info("Starting reset device data...")
        reset_data(telegram.udid, telegram.TELEGRAM_ADB_NAME, telegram.app_prefix)
        logging.info("Device data reset successfully.")

        vpn = VPN()
        if NEED_CHANGE_LOCATION:
            vpn.change_location(COUNTRY)
            NEED_CHANGE_LOCATION = False
        else:
            vpn.reconnection()

        telegram.start_messenger()

        number_info = phone_number_send(telegram, sms_obj)
        if not number_info:
            return False
        if number_info == "shut_down":
            return False

        activation_id = number_info[0]
        phone_number = number_info[1]
        number_price = number_info[2]
        username = None
        password = None

        if telegram.check_element(By.XPATH, telegram.ENTER_CODE_TEXT, timeout=2):
            logging.info("No email required, waiting for SMS code")
        else:
            # Register with email
            logging.info("Email required. Starting OnionMail registration")
            username = generate_random_string(12)
            password = generate_random_string(16)

            email_address = onion.reg_and_login(username=username, password=password)
            if not email_address:
                logging.error("Failed to register or login OnionMail")
                return False

            logging.info(f"OnionMail registered and logged in with email: {email_address}")
            logging.info("Waiting for confirmation email...")

            cech_data = setup_cech()
            first_name = random.choice(first_names) if first_names else "Unknown"
            last_name = random.choice(last_names) if last_names else "Unknown"

            # Update cech_data with new email registration info
            cech_data['email'] = email_address
            cech_data['username'] = username
            cech_data['password'] = password
            cech_data['first_name'] = first_name
            cech_data['last_name'] = last_name
            cech_data['phone_number'] = phone_number
            cech_data['number_price'] = number_price

            write_json(cech_data, CECH_PATH)

            try:
                telegram.input_phone_number(phone_number)
                logging.info(f"Phone number {phone_number} sent to Telegram for email-based registration")
            except Exception as e:
                logging.error(f"Failed to send phone number to Telegram: {str(e)}")
                return False

        # Waiting for SMS code
        logging.info("Waiting for SMS code...")
        code = sms_obj.check_verif_status(activation_id, timeout=300)
        if not code:
            logging.error("SMS code not received, performing activation_admin")
            activation_admin(sms_obj, last_names, phone_number, activation_id)
            return False

        try:
            telegram.check_enter_code_text()
            # Enter SMS code
            try:
                telegram.send_keys(By.XPATH, telegram.ENTER_CODE_TEXT, code)
            except Exception:
                telegram.send_keys(By.XPATH, telegram.ENTER_CODE_TEXT, code)

            logging.info("SMS code entered successfully")

            # Check and handle 2FA
            if check_2fa(telegram):
                logging.info("2FA detected and handled (email reset flow)")
            else:
                logging.info("No 2FA detected")

        except Exception as e:
            logging.error(f"Failed to enter or process SMS code: {str(e)}")
            return False

        # Create TData and Telethon session
        logging.info("Creating TData with Telegram Desktop...")
        tdata_folder = create_tdata_with_telegram_desktop(phone_number, telegram)
        logging.info(f"TData folder created at {tdata_folder}")

        logging.info("Creating Telethon session...")
        session_result = asyncio.run(create_session_with_telethon(phone_number, telegram))
        if not session_result:
            logging.error("Failed to create Telethon session")
            return False

        session_path, session_tdata_dir = session_result

        # Save session and related data
        save_session(
            phone_number=phone_number,
            device_info=device_info,
            number_price=number_price,
            session_path=session_path
        )

        if FOLDER_NAME_WITH_ACCOUNTS is None:
            FOLDER_NAME_WITH_ACCOUNTS = os.path.dirname(tdata_folder)

        logging.info(f"Account registered and session saved for {phone_number}")
        return True

    except Exception as e:
        logging.error(f"Error during account registration for attempt {attempt}: {e}")
        return False

    finally:
        telegram.close()
        onion.close()


def main():
    """CLI entrypoint: read config, ask for basic parameters and run the loop.

    It picks a device (emulator or physical), wires the SMS provider
    and sequentially calls register_telegram_account() until the
    requested number of accounts is reached or a fatal error occurs.
    """
    cech_data = setup_cech()
    start_time = time.time()

    registered_accounts = 0
    try:
        sms_api_key_path = CONFIG['sms_api']['api_key_path']
        if not sms_api_key_path:
            sms_api_key_path = 'sms_activate_api.txt'
        sms_service = CONFIG['sms_api']['service_name']
        cech_data['sms_api_key_path'] = sms_api_key_path
        write_json(cech_data, CECH_PATH)

        device_type = CONFIG['adb']['device_type']
        while device_type not in ['E', 'P']:
            print("Invalid input. Please enter 'E' for emulator or 'P' for physical device.")
            device_type = input("Enter 'E' for emulator or 'P' for physical device: ").strip().upper()
        is_physical = device_type == 'P'

        first_names_file = CONFIG['profiles'].get('first_names_file', '')
        last_names_file = CONFIG['profiles'].get('last_names_file', '')
        first_names = load_names(first_names_file) if os.path.isfile(first_names_file) else []
        last_names = load_names(last_names_file) if os.path.isfile(last_names_file) else []

        num_accounts = int(input("Enter number of accounts to register: "))

        try:
            devices = get_device_config(1, is_physical)  # Single thread
        except ValueError as e:
            logging.error(f"Configuration error: {str(e)}")
            return

        attempt = 0
        device_config = devices[0]  # Only one device config

        # Sequential execution for each account
        while registered_accounts < num_accounts:
            attempt += 1
            logging.info(f"Attempting to register account {attempt}")
            success = register_telegram_account(device_config, sms_service, sms_api_key_path, first_names, last_names, attempt)
            if success:
                registered_accounts += 1
                logging.info(f"Account registration successful. Total successful: {registered_accounts}/{num_accounts}")
            else:
                logging.error(f"Account registration failed for attempt {attempt}")

    except Exception as e:
        logging.error(f"Error in main loop: {str(e)}")
    finally:
        if 'device_config' in locals():
            if not device_config.get('is_physical') and device_config.get('app_name'):
                kill_emulator(device_config['app_name'])
        elapsed_time = time.time() - start_time

        if registered_accounts > 0:
            per_account = elapsed_time / registered_accounts
        else:
            per_account = 0

        today = datetime.now().strftime('%Y-%m-%d')

        if FOLDER_NAME_WITH_ACCOUNTS:
            subprocess.run(
                f'scp -r {FOLDER_NAME_WITH_ACCOUNTS} {CONFIG["server"]["user"]}@{CONFIG["server"]["host"]}:{CONFIG["server"]["temp_path"]}',
                shell=True
            )

            subprocess.run(
                f'ssh {CONFIG["server"]["user"]}@{CONFIG["server"]["host"]} "docker run --rm -v {CONFIG["server"]["temp_path"]}/{today}_{COUNTRY}:/data {CONFIG["server"]["docker_image"]} /data"',
                shell=True
            )

        print(f"Скрипт выполнен за {(elapsed_time / 60):.2f} минут")
        print(f"Среднее время на 1 аккаунт {(per_account / 60):.2f} минут")


if __name__ == "__main__":
    main()
