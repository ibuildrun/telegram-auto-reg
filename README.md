<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Windows">
  <img src="https://img.shields.io/badge/Appium-2.0-662D91?style=for-the-badge&logo=appium&logoColor=white" alt="Appium">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
</p>

<h1 align="center">
  <br>
  <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/telegram/telegram-original.svg" alt="Telegram" width="80">
  <br>
  Telegram Auto-Regger
  <br>
</h1>

<h4 align="center">🚀 End-to-end automation pipeline for Telegram account registration</h4>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-configuration">Configuration</a> •
  <a href="#-usage">Usage</a> •
  <a href="#-roadmap">Roadmap</a>
</p>

<p align="center">
  <img src="https://user-images.githubusercontent.com/placeholder/demo.gif" alt="Demo" width="700">
</p>

---

> [!IMPORTANT]
> This project is a **technical portfolio piece** for educational purposes and demonstrating automation skills.
> You are solely responsible for respecting Telegram's Terms of Service and local laws.

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 📱 Android Automation
- Full Telegram UI automation via **Appium**
- Device fingerprint randomization (IMEI, Android ID, MAC)
- Support for emulators (LDPlayer) and physical devices
- ADB-based device management

</td>
<td width="50%">

### 🖥️ Windows Automation
- **ExpressVPN** control for IP rotation
- **Onion Mail** registration via Chrome
- **Telegram Desktop** TData extraction
- pywinauto-based UI automation

</td>
</tr>
<tr>
<td width="50%">

### 📨 SMS Integration
- **SMS-Activate** API support
- **GrizzlySMS** API support
- Automatic code extraction
- Cost tracking and statistics

</td>
<td width="50%">

### 💾 Session Management
- Telethon `.session` files
- Telegram Desktop `tdata` folders
- Session conversion utilities
- Metadata persistence (JSON)

</td>
</tr>
</table>

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        📱 DEVICE LAYER                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │
│  │  LDPlayer   │  │  Physical   │  │    ADB      │                  │
│  │  Emulator   │  │   Device    │  │  Commands   │                  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                  │
└─────────┼────────────────┼────────────────┼─────────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      🤖 AUTOMATION LAYER                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │     Appium      │  │    pywinauto    │  │    Telethon     │     │
│  │  (Android UI)   │  │  (Windows UI)   │  │  (Telegram API) │     │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘     │
└───────────┼────────────────────┼────────────────────┼───────────────┘
            │                    │                    │
            ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      🔧 SERVICE LAYER                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │ SMS API  │  │  Onion   │  │   VPN    │  │ TDesktop │            │
│  │ Provider │  │   Mail   │  │ Control  │  │  Export  │            │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘            │
└───────┼─────────────┼─────────────┼─────────────┼───────────────────┘
        │             │             │             │
        ▼             ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    📊 ORCHESTRATION LAYER                            │
│                                                                      │
│                    ┌─────────────────────┐                          │
│                    │  telegram_regger.py │                          │
│                    │    (Main Script)    │                          │
│                    └─────────────────────┘                          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Windows 10/11**
- **ADB** (Android Debug Bridge)
- **Appium Server**
- Android emulator (LDPlayer recommended) or physical device

### Installation

```bash
# Clone the repository
git clone https://github.com/ibuildrun/telegram-auto-reg.git
cd telegram-auto-reg

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install GitHub dependencies
pip install git+https://github.com/ntqbit/tdesktop-decrypter.git
```

### Verify Setup

```bash
# Check ADB connection
adb devices

# Should show your device/emulator
# List of devices attached
# 127.0.0.1:5555    device
```

---

## ⚙️ Configuration

Create `config.yaml` from the example:

```bash
cp config.yaml.example config.yaml
```

### Minimal Configuration

```yaml
# config.yaml
adb:
  device_type: "E"              # E = emulator, P = physical
  device_udid: "127.0.0.1:5555" # from `adb devices`
  appium_port: 4723

sms_api:
  service_name: "sms-activate"
  api_key_path: "sms_activate_api.txt"

profiles:
  first_names_file: "data/first_names.txt"
  last_names_file: "data/last_names.txt"
```

<details>
<summary>📋 Full Configuration Reference</summary>

```yaml
# ADB & Device Settings
adb:
  device_type: "E"                    # E = emulator, P = physical device
  device_udid: "127.0.0.1:5555"       # Device ID from `adb devices`
  appium_port: 4723                   # Appium server port
  adb_path: "C:\\Android\\platform-tools\\adb.exe"

# SMS Provider
sms_api:
  service_name: "sms-activate"        # or "grizzly-sms"
  api_key_path: "sms_activate_api.txt"

# Profile Generation
profiles:
  first_names_file: "data/first_names.txt"
  last_names_file: "data/last_names.txt"

# Telethon API (get from my.telegram.org)
telethon:
  api_id: 123456
  api_hash: "your_api_hash_here"
  device_model: "Desktop"
  system_version: "Windows 10"
  app_version: "4.0.4 x64"

# Remote Server (optional)
server:
  user: "deploy"
  host: "server.example.com"
  temp_path: "/tmp/accounts"
  docker_image: "account-processor:latest"
```

</details>

---

## 📖 Usage

### Start Registration

```bash
python telegram_regger.py
```

You'll be prompted for:
- **Country** — `USA`, `United Kingdom`, etc.
- **Max price** — Maximum SMS cost
- **Number of accounts** — How many to register

### Registration Flow

```
1. 📱 Prepare Device
   └─ Reset Telegram data
   └─ Randomize device fingerprint
   └─ Connect VPN

2. 📞 Get Phone Number
   └─ Rent from SMS provider
   └─ Validate country code
   └─ Send to Telegram app

3. 📧 Email Verification (if required)
   └─ Register Onion Mail
   └─ Wait for confirmation

4. ✅ Complete Registration
   └─ Receive SMS code
   └─ Enter in Telegram
   └─ Handle 2FA if needed

5. 💾 Export Sessions
   └─ Create Telethon session
   └─ Extract TData folder
   └─ Save metadata
```

### Output Structure

```
sessions/
├── converted/
│   └── 2025-01-15/
│       └── +79001234567.json    # Account metadata
├── tg_desk/
│   └── +79001234567/
│       └── tdata/               # Telegram Desktop data
└── telethon/
    └── +79001234567/
        └── +79001234567.session # Telethon session
```

---

## 📁 Project Structure

```
telegram-auto-reg/
├── 📂 auto_reger/              # Core automation modules
│   ├── 📂 emulator/            # Appium automation
│   │   ├── base.py             # Emulator base class
│   │   ├── telegram.py         # Telegram UI automation
│   │   └── instagram.py        # Instagram automation
│   ├── 📂 windows/             # Windows automation
│   │   ├── base.py             # App base class
│   │   ├── onion.py            # Onion Mail
│   │   ├── vpn.py              # ExpressVPN
│   │   └── telegram_desktop.py # Telegram Desktop
│   ├── adb.py                  # ADB commands
│   ├── sms_api.py              # SMS provider wrapper
│   ├── sessions.py             # Session converters
│   ├── tdesktop.py             # TData tools
│   └── utils.py                # Utilities
├── 📂 tests/                   # Test suite
├── telegram_regger.py          # Main script
├── config.yaml.example         # Config template
├── requirements.txt            # Dependencies
└── README.md
```

---

## 🗺️ Roadmap

<table>
<tr>
<td>

### ✅ Completed
- [x] Android automation (Appium)
- [x] Windows automation (pywinauto)
- [x] SMS provider integration
- [x] Session management
- [x] Device fingerprinting
- [x] Modular architecture

</td>
<td>

### 🚧 In Progress
- [ ] TUI interface (Textual)
- [ ] SOCKS5 proxy support
- [ ] FirstMail integration
- [ ] SMS provider plugins
- [ ] Config validation

</td>
<td>

### 📋 Planned
- [ ] Docker support
- [ ] Multi-threading
- [ ] Statistics dashboard
- [ ] API server mode
- [ ] Dry-run mode

</td>
</tr>
</table>

---

## 🛠️ Tech Stack

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Appium-662D91?style=flat-square&logo=appium&logoColor=white" alt="Appium">
  <img src="https://img.shields.io/badge/Selenium-43B02A?style=flat-square&logo=selenium&logoColor=white" alt="Selenium">
  <img src="https://img.shields.io/badge/ADB-3DDC84?style=flat-square&logo=android&logoColor=white" alt="ADB">
</p>

| Category | Technologies |
|----------|-------------|
| **Telegram API** | Telethon |
| **Android** | Appium, Selenium, ADB |
| **Windows** | pywinauto, pyautogui, pywin32 |
| **SMS** | smsactivate API |
| **Config** | PyYAML |
| **Image/OCR** | Pillow, pytesseract |

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <sub>
    Made with ❤️ by <a href="https://github.com/ibuildrun"><b>@ibuildrun</b></a>
  </sub>
</p>

<p align="center">
  <sub>
    ⭐ Star this repo if you find it useful!
  </sub>
</p>

<p align="center">
  <a href="https://github.com/ibuildrun/telegram-auto-reg/issues">Report Bug</a>
  •
  <a href="https://github.com/ibuildrun/telegram-auto-reg/issues">Request Feature</a>
</p>
