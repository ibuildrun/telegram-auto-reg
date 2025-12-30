# Telegram Auto-Regger (Automation Showcase)

> End-to-end automation pipeline that orchestrates Android emulators / devices, Appium, ADB, SMS providers, a custom email service, VPN, and Telethon to register and warm up Telegram accounts.

> 🧩 **Important note**  
> This project is a **technical portfolio piece**. It is intended for educational purposes and for demonstrating automation skills (Python, Telethon, Appium, UI automation, ADB, external APIs).  
> You are solely responsible for respecting Telegram’s Terms of Service, the SMS provider’s rules, and local laws. Do **not** use this project for spam, abuse, or any form of malicious activity.

---

## Table of contents

- [Overview](#overview)
- [Core features](#core-features)
- [Architecture](#architecture)
  - [High-level flow](#high-level-flow)
  - [Modules](#modules)
- [Project structure](#project-structure)
- [Installation](#installation)
  - [Python dependencies](#python-dependencies)
  - [Additional GitHub dependencies](#additional-github-dependencies)
- [Configuration](#configuration)
  - [`config.yaml`](#configyaml)
- [Usage](#usage)
- [Notes & limitations](#notes--limitations)
- [Roadmap / ideas](#roadmap--ideas)
- [License](#license)

---

## Overview

This repository implements a **full automation pipeline** for Telegram registration:

- Controls **Android emulators or physical devices** via ADB + Appium.
- Uses a **third-party SMS provider** (e.g. sms-activate / GrizzlySMS) to rent numbers and fetch SMS codes.
- Optionally registers a mailbox on **Onion Mail** (through Windows UI automation) when Telegram requires an email step.
- Uses **ExpressVPN** GUI automation to rotate IPs or switch locations.
- Builds both **Telethon sessions** and **Telegram Desktop TData** for each registered account.

The main script is `telegram_regger.py`. It ties together all subsystems and can serve as a real-world example of complex automation/orchestration in Python.

---

## Core features

- ✅ Automation of Telegram registration flow (number → SMS → login)
- ✅ Android device / emulator control via **ADB** and **Appium**
- ✅ Windows UI automation:
  - Onion Mail (Chrome) – register/login mailbox, fetch email codes
  - ExpressVPN – reconnect or change country
  - Telegram Desktop – input phone number and login code
- ✅ SMS provider integration via **smsactivate** compatible API
- ✅ Session & credentials management:
  - Telethon `.session` files
  - Telegram Desktop `tdata` folders
  - Optional conversion between TData / auth keys / Telethon sessions
- ✅ Device “fingerprint” randomisation (IMEI, Android ID, user-agent, timezone, etc.)
- ✅ Simple local stats tracking via JSON (success/fail reasons, costs, etc.)

---

## Architecture

### High-level flow

For each account, the pipeline roughly looks like this:

1. **Prepare device**
   - Connect to Android device/emulator via ADB.
   - Reset Telegram data and various device identifiers (`auto_reger.adb.reset_data`).
   - Optionally change VPN location or reconnect.

2. **Buy number & send to Telegram**
   - Use `SmsApi` (smsactivate-compatible) to rent a phone number.
   - Validate country code, send the number to Telegram on the Android device via Appium (`Telegram.input_phone_number`).

3. **Email (optional)**
   - If Telegram demands an email, automate Onion Mail in Chrome:
     - Register mailbox.
     - Login and wait for confirmation mail.
   - Provide email back to Telegram if required by flow.

4. **Receive SMS and complete registration**
   - Poll SMS provider for the verification code (`SmsApi.check_verif_status`).
   - Enter SMS code in Telegram (Android UI).
   - Handle possible 2FA (two-step verification) UI screens.

5. **Create sessions / TData**
   - Launch Telegram Desktop on Windows with a clean profile.
   - Input phone number, read SMS from Android Telegram if needed, log in.
   - Save resulting TData folder (`auto_reger.tdesktop`, `auto_reger.sessions`).
   - Build Telethon `.session` file for programmatic access.

6. **Store metadata**
   - Persist account info (phone number, device info, SMS cost, session paths) into JSON under `sessions/converted/…`.

All of this is orchestrated from `telegram_regger.py`.

---

### Modules

**Key modules inside `auto_reger/`:**

- `adb.py`  
  Low-level helpers for ADB:
  - Connect to device (`connect_adb`)
  - Query device info (model, Android version, Telegram version)
  - Randomise identifiers (Android ID, IMEI, MAC, timezone, etc.)
  - `reset_data(...)` – high-level reset of Telegram and related settings.

- `emulator.py`  
  Appium-based Android automation:
  - `Emulator` – base class (emulator/device, Appium service, WebDriver)
  - `Telegram` – Telegram Android UI automation (enter phone number, read SMS, navigate settings, set avatar, etc.)
  - `Instagram` (optional) – similar pattern for Instagram Lite.

- `windows_automation.py`  
  Windows desktop automation via pywinauto + pyautogui:
  - `App` – base class (start/attach to app, close, kill background processes)
  - `Onion` – work with Onion Mail in Chrome (register, login, extract codes)
  - `VPN` – control ExpressVPN (reconnect, change location)
  - `TelegramDesktop` – drive Telegram Desktop login (enter phone, code).

- `sms_api.py`  
  Wrapper around `smsactivate.api.SMSActivateAPI`:
  - Supports sms-activate / GrizzlySMS handler API.
  - Country resolution, price checks, renting numbers (`verification_number`).
  - Polling for codes (`check_verif_status`).
  - Local tracking of activations in `activations.json`.

- `tdesktop.py`  
  Tools around **Telegram Desktop TData**:
  - Decrypt and parse TData via `tdesktop_decrypter`.
  - Extract `auth_key`, `dc_id`, `user_id` for accounts.
  - Batch process a folder of accounts and generate a JSON summary.

- `sessions.py`  
  Session management & converters:
  - Convert TData ↔ Telethon sessions.
  - Work with raw `auth_key` + `dc_id` to define Telethon clients.
  - Android `tgnet.dat` + `userconfig.xml` → Telethon session or TData.
  - Helper `set_2fa_safe(...)` to set/reset cloud password via Telethon.

- `utils.py`  
  Shared utilities:
  - `PROJECT_ROOT`, `load_config()`, `CONFIG`
  - JSON read/write, reading text lists, name lists
  - Device config loader (`get_device_config`)
  - Emulator process kill helper (`kill_emulator`)
  - Random string generation, avatar download, etc.

**Top-level script:**

- `telegram_regger.py`  
  The main orchestration script:
  - CLI inputs (country, max price, number of accounts).
  - Loads `config.yaml`.
  - Picks device config (emulator / physical).
  - Repeatedly calls `register_telegram_account(...)`.

---

## Project structure

Example repository layout:

```text
Telegrm-Auto-Regger/
├─ auto_reger/
│  ├─ __init__.py
│  ├─ adb.py
│  ├─ emulator.py
│  ├─ sessions.py
│  ├─ sms_api.py
│  ├─ tdesktop.py
│  ├─ utils.py
│  └─ windows_automation.py
├─ sessions/
│  ├─ converted/
│  ├─ tg_desk/
│  └─ telethon/
├─ telegram_regger.py
├─ requirements.txt
├─ config.yaml              # not committed; use config.yaml.example instead
├─ config.yaml.example      # template config for users
├─ activations.json         # created at runtime
├─ cech.json                # simple stats storage
└─ README.md
```

---

## Installation

### Option 1: Download Pre-built Executable (Recommended)

Download the latest `TelegramAutoReg.exe` from [Releases](https://github.com/ibuildrun/telegram-auto-reg/releases).

No Python installation required! Just:
1. Download `TelegramAutoReg.exe`
2. Copy `config.yaml.example` to `config.yaml` and configure
3. Run the executable

### Option 2: Run from Source

### Python dependencies

Requirements:

- Python **3.10+**
- Windows 10/11 (for desktop automation)
- ADB installed and available (or path configured in `config.yaml`)
- Android emulator or physical device with USB debugging enabled

Create a virtual environment and install Python deps:

```bash
git clone https://github.com/ltrix07/Telegrm-Auto-Regger.git
cd Telegrm-Auto-Regger

python -m venv .venv
.venv\Scripts\activate  # on Windows

pip install --upgrade pip
pip install -r requirements.txt
```

Typical `requirements.txt` (simplified):

```text
telethon
requests
PyYAML
psutil
pyautogui
pywinauto
pywin32
Pillow
pytesseract
Appium-Python-Client
selenium
schedule
cryptography
smsactivate
```

### Additional GitHub dependencies

Some modules used in this project are **not** on PyPI and should be installed from GitHub (or included as submodules):

- `tdesktop_decrypter` – Telegram Desktop TData decrypter  
- `AndroidTelePorter` – Android Telegram session converter  
- `TGConvertor` – TData → Telethon converter

Example (adapt to your actual repos/URLs):

```bash
pip install git+https://github.com/ntqbit/tdesktop-decrypter.git
# pip install git+https://github.com/<user>/AndroidTelePorter.git
# pip install git+https://github.com/<user>/TGConvertor.git
```

If you plan to *only* use parts of the project (e.g. just Android automation + SMS), you can omit some of these extras.

---

## Configuration

### `config.yaml`

The project reads configuration from `config.yaml` located in the repository root.

Minimal example:

```yaml
adb:
  # E = emulator, P = physical device
  device_type: "E"
  device_udid: "127.0.0.1:5555"   # from `adb devices`
  appium_port: 4723
  adb_path: "C:\Android\platform-tools\adb.exe"

sms_api:
  # "sms-activate" or "grizzly-sms"
  service_name: "sms-activate"
  # file with API key (single line)
  api_key_path: "sms_activate_api.txt"

profiles:
  # text files with one name per line (optional)
  first_names_file: "data/first_names.txt"
  last_names_file: "data/last_names.txt"

server:
  # optional: remote server for syncing sessions via scp/docker
  user: "user"
  host: "example.com"
  temp_path: "/tmp/telegram-sessions"
  docker_image: "my/docker-image:latest"

telethon:
  api_id: 123456
  api_hash: "YOUR_API_HASH"
  telegram_device_model: "Android"
  telegram_system_version: "9"
  telegram_app_version: "10.0"
```

You can commit a `config.yaml.example` file to the repo and keep your real `config.yaml` out of version control.

---

## Usage

> ⚠️ **Warning**  
> Running the script will contact real external services:
> - SMS provider (credits will be spent),
> - Telegram servers,
> - optionally a VPN service and email provider.  
> Use on test accounts and at your own risk. Always respect the terms of the services you use.

1. Make sure:

   - `config.yaml` is properly filled.
   - ADB sees your device/emulator:
     ```bash
     adb devices
     ```
   - Appium Server is available (or the `Emulator` class starts it automatically on the configured port).

2. Run the application:

   ```bash
   .venv\Scripts\activate
   
   # Modern TUI interface (recommended)
   py -m cli
   
   # Or classic script
   python telegram_regger.py
   ```

3. Follow the CLI prompts:

   - **Country** for registration (`USA`, `United Kingdom`, …).
   - **Maximum price** per number.
   - **Number of accounts** to register.

4. The script will:

   - Prepare device / emulator.
   - Rotate VPN if configured.
   - Rent a number, send it to Telegram.
   - Handle email step via Onion Mail (when required).
   - Wait for SMS and complete registration.
   - Create Telethon session and/or TData.
   - Save all metadata into `sessions/…` and `cech.json`.

If something goes wrong, check:

- `telegram_regger.log` – detailed runtime logs.
- `cech.json` – simple aggregated stats.
- `activations.json` – currently tracked SMS activations.

---

## Building Executable

To create a standalone `.exe` file that doesn't require Python:

### Prerequisites

```bash
pip install pyinstaller
```

### Build

```bash
# Simple build
python build.py

# Or manually
pyinstaller TelegramAutoReg.spec
```

The executable will be created in `dist/TelegramAutoReg.exe` (~50-100 MB).

### Custom Icon

Place your icon file at `assets/icon.ico` before building. Recommended size: 256x256.

### Distribution

To distribute the application:
1. Build the `.exe`
2. Include `config.yaml.example` alongside the executable
3. Users just need to:
   - Rename `config.yaml.example` to `config.yaml`
   - Fill in their API keys
   - Run `TelegramAutoReg.exe`

---

## Notes & limitations

- The code is tightly coupled to **Windows UI** (Telegram Desktop, ExpressVPN, Chrome) and coordinates / titles in a specific language (often Russian). For a different OS or locale you’ll need to adjust locators and selectors.
- Device “fingerprint” logic uses ADB + root commands. It assumes:
  - Rooted emulator/device,
  - Correct ADB path,
  - Proper permissions.
- SMS provider integration assumes **sms-activate handler API** compatibility.
- Some parts (e.g. TData decryption, Android `tgnet.dat` conversion) rely on external libraries that must be installed separately from GitHub.
- This project is not a polished library yet; it’s a **working automation lab**. The code is intentionally kept verbose and explicit to show how the pieces fit together.

---

## Roadmap / ideas

Potential future improvements:

- [ ] Refactor `telegram_regger.py` into smaller CLI commands (`scripts/`):
  - `register_account.py`
  - `convert_sessions.py`
  - `collect_stats.py`
- [ ] Add Dockerfile for server-side processing and CI examples.
- [ ] Add tests (unit/integration) for individual modules (`auto_reger/…`).
- [ ] Add a “dry-run” mode (no real SMS/VPN/email calls).
- [ ] Make Windows automation more robust by relying less on coordinates and more on accessibility names.

---

If you’re reading this on GitHub and want to dive deeper, start from:

- `auto_reger/emulator.py` (Android + Telegram automation)
- `auto_reger/windows_automation.py` (Onion Mail / VPN / Telegram Desktop)
- `auto_reger/sessions.py` (TData / Telethon session logic)
- `telegram_regger.py` (orchestration script)
