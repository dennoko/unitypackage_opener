# ...existing code...
import json
import os
from dataclasses import dataclass, asdict
from typing import Literal

SETTINGS_DIR = os.path.join(os.path.expanduser("~"), ".unitypackage_opener")
SETTINGS_PATH = os.path.join(SETTINGS_DIR, "settings.json")

ConflictPolicy = Literal["overwrite", "skip", "rename"]
Mode = Literal["merge", "individual"]
OutputDirMode = Literal["auto", "fixed"]


@dataclass
class AppSettings:
    mode: Mode = "individual"
    conflict: ConflictPolicy = "rename"
    output_dir: str = os.path.join(os.path.expanduser("~"), "Desktop")
    output_dir_mode: OutputDirMode = "auto"
    last_exe_path: str | None = None


_default = AppSettings()


def ensure_settings_dir():
    os.makedirs(SETTINGS_DIR, exist_ok=True)


def load_settings() -> AppSettings:
    ensure_settings_dir()
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                merged = {**asdict(_default), **data}
                return AppSettings(**merged)
        except Exception:
            return _default
    return _default


def save_settings(s: AppSettings):
    ensure_settings_dir()
    with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
        json.dump(asdict(s), f, indent=2, ensure_ascii=False)
