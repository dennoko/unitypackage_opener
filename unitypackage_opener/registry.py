import json
import os
import sys
from typing import Optional
import winreg


APP_NAME = "unitypackage_opener"
# Register under SystemFileAssociations for .unitypackage
CONTEXT_MENU_KEY = r"Software\\Classes\\SystemFileAssociations\\.unitypackage\\shell\\Open with unitypackage_opener"
COMMAND_KEY = CONTEXT_MENU_KEY + r"\\command"

EXT_KEY = r"Software\\Classes\\.unitypackage"
PROGID = "Unitypackage"

SETTINGS_DIR = os.path.join(os.path.expanduser("~"), ".unitypackage_opener")
SETTINGS_PATH = os.path.join(SETTINGS_DIR, "settings.json")


def get_executable_path() -> str:
    if getattr(sys, 'frozen', False):
        return sys.executable
    else:
        return os.path.abspath(sys.argv[0])


def ensure_settings_dir():
    os.makedirs(SETTINGS_DIR, exist_ok=True)


def load_settings() -> dict:
    ensure_settings_dir()
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_settings(data: dict):
    ensure_settings_dir()
    with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def register_extension_progid():
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, EXT_KEY) as key:
        winreg.SetValueEx(key, None, 0, winreg.REG_SZ, PROGID)
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{PROGID}") as key:
        winreg.SetValueEx(key, None, 0, winreg.REG_SZ, "Unity Package")


def register_context_menu(exe_path: Optional[str] = None):
    if exe_path is None:
        exe_path = get_executable_path()

    # No need to set extension progid for SystemFileAssociations
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, CONTEXT_MENU_KEY) as key:
        winreg.SetValueEx(key, None, 0, winreg.REG_SZ, f"Open with {APP_NAME}")
        try:
            winreg.SetValueEx(key, "MultiSelectModel", 0, winreg.REG_SZ, "Player")
        except Exception:
            pass
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, COMMAND_KEY) as key:
        # Always launch with --headless for context menu
        command = f'"{exe_path}" --headless %1'
        winreg.SetValueEx(key, None, 0, winreg.REG_SZ, command)


def ensure_registered():
    settings = load_settings()
    current_path = get_executable_path()
    prev_path = settings.get("last_exe_path")

    if prev_path != current_path:
        # Remove previous registration if exe path changed
        try:
            # Remove old context menu and command keys if they exist
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, CONTEXT_MENU_KEY, 0, winreg.KEY_WRITE) as key:
                pass
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, COMMAND_KEY)
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, CONTEXT_MENU_KEY)
        except Exception:
            pass
        register_context_menu(current_path)
        settings["last_exe_path"] = current_path
        save_settings(settings)

    return settings
