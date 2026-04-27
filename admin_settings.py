import json
import os
import sys
from typing import Any, Dict

_SETTINGS_CACHE: Dict[str, Any] | None = None


def _is_frozen_windows() -> bool:
    return os.name == "nt" and bool(getattr(sys, "frozen", False))


def _base_settings_dir() -> str:
    if _is_frozen_windows():
        local_appdata = os.getenv("LOCALAPPDATA") or os.path.expanduser("~")
        return os.path.join(local_appdata, "CaseCreator")
    return os.path.dirname(os.path.abspath(__file__))


def _ensure_settings_dir() -> None:
    os.makedirs(_base_settings_dir(), exist_ok=True)


def _settings_path() -> str:
    return os.path.join(_base_settings_dir(), "admin_settings.json")


def load_admin_settings() -> Dict[str, Any]:
    """
    Load admin_settings.json from project root.
    Returns {} when file is missing, malformed, unreadable, or not an object.
    """
    path = _settings_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except FileNotFoundError:
        return {}
    except Exception:
        return {}
    return {}


def _cached_settings() -> Dict[str, Any]:
    global _SETTINGS_CACHE
    if _SETTINGS_CACHE is None:
        _SETTINGS_CACHE = load_admin_settings()
    return _SETTINGS_CACHE


def get_admin_setting(key: str, default: Any) -> Any:
    """
    Return admin override for key only when it is a non-empty value.
    Otherwise return default.
    """
    settings = _cached_settings()
    value = settings.get(key)
    if isinstance(value, str):
        return value if value.strip() else default
    if value is None:
        return default
    return value


def save_admin_settings_updates(updates: Dict[str, Any]) -> str:
    """
    Merge updates into admin_settings.json while preserving unrelated keys.
    Returns the settings file path.
    """
    path = _settings_path()
    _ensure_settings_dir()
    current = load_admin_settings()
    if not isinstance(current, dict):
        current = {}

    merged = dict(current)
    merged.update(updates or {})

    temp_path = path + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=True)
        f.write("\n")
    os.replace(temp_path, path)

    global _SETTINGS_CACHE
    _SETTINGS_CACHE = merged
    return path
