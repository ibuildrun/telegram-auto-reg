#!/usr/bin/env python
"""
Build script for Telegram Auto-Regger
Creates standalone .exe file using PyInstaller

Usage:
    python build.py          # Build .exe
    python build.py --clean  # Clean build artifacts
    python build.py --test   # Test the built .exe
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# Project paths
ROOT = Path(__file__).parent
DIST_DIR = ROOT / "dist"
BUILD_DIR = ROOT / "build"
SPEC_FILE = ROOT / "TelegramAutoReg.spec"
EXE_NAME = "TelegramAutoReg.exe"


def clean():
    """Remove build artifacts."""
    print("[*] Cleaning build artifacts...")
    
    for folder in [DIST_DIR, BUILD_DIR]:
        if folder.exists():
            shutil.rmtree(folder)
            print(f"    Removed {folder}")
    
    # Remove __pycache__ folders
    for pycache in ROOT.rglob("__pycache__"):
        shutil.rmtree(pycache)
    
    print("[+] Clean complete!")


def check_dependencies():
    """Check if required build tools are installed."""
    print("[*] Checking dependencies...")
    
    try:
        import PyInstaller
        print(f"    PyInstaller: {PyInstaller.__version__}")
    except ImportError:
        print("[-] PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    try:
        import customtkinter
        print(f"    customtkinter: {customtkinter.__version__}")
    except ImportError:
        print("[-] customtkinter not found. Please install: pip install customtkinter")
        sys.exit(1)
    
    print("[+] Dependencies OK!")


def create_version_info():
    """Create Windows version info file."""
    version_info = '''
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          u'040904B0',
          [
            StringStruct(u'CompanyName', u'ibuildrun'),
            StringStruct(u'FileDescription', u'Telegram Auto-Regger'),
            StringStruct(u'FileVersion', u'1.0.0'),
            StringStruct(u'InternalName', u'TelegramAutoReg'),
            StringStruct(u'LegalCopyright', u'2024 ibuildrun'),
            StringStruct(u'OriginalFilename', u'TelegramAutoReg.exe'),
            StringStruct(u'ProductName', u'Telegram Auto-Regger'),
            StringStruct(u'ProductVersion', u'1.0.0'),
          ]
        )
      ]
    ),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''
    version_file = ROOT / "version_info.txt"
    version_file.write_text(version_info.strip(), encoding='utf-8')
    print("   Created version_info.txt")


def build():
    """Build the .exe file."""
    print("\n[*] Building TelegramAutoReg.exe...")
    print("=" * 50)
    
    check_dependencies()
    create_version_info()
    
    # Run PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        str(SPEC_FILE)
    ]
    
    print(f"\n[*] Running: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd, cwd=ROOT)
    
    if result.returncode != 0:
        print("\n[-] Build failed!")
        sys.exit(1)
    
    # Check output
    exe_path = DIST_DIR / EXE_NAME
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print("\n" + "=" * 50)
        print(f"[+] Build successful!")
        print(f"    Output: {exe_path}")
        print(f"    Size: {size_mb:.1f} MB")
        print("=" * 50)
        
        # Copy config example next to exe
        config_example = ROOT / "config.yaml.example"
        if config_example.exists():
            shutil.copy(config_example, DIST_DIR / "config.yaml.example")
            print(f"    Copied config.yaml.example to dist/")
        
        print(f"\n[>] To run: {exe_path}")
    else:
        print("\n[-] Build failed - exe not found!")
        sys.exit(1)


def test_exe():
    """Test if the built exe runs."""
    exe_path = DIST_DIR / EXE_NAME
    
    if not exe_path.exists():
        print(f"[-] {exe_path} not found. Run 'python build.py' first.")
        sys.exit(1)
    
    print(f"[*] Testing {exe_path}...")
    
    # Just check if it starts (will open GUI)
    subprocess.Popen([str(exe_path)])
    print("[+] Application started!")


def main():
    args = sys.argv[1:]
    
    if "--clean" in args:
        clean()
    elif "--test" in args:
        test_exe()
    else:
        if "--clean" not in args:
            clean()
        build()


if __name__ == "__main__":
    main()
