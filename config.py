# --- config.py ---

import os
from admin_settings import get_admin_setting
from local_settings import get_setting

# Project-root-relative defaults for bundled assets
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_SIGNATURE_DOCTORS_PATH = os.path.join(_PROJECT_ROOT, "List of Signature Dr.xlsx")
_DEFAULT_TEMPLATE_DIR = os.path.join(_PROJECT_ROOT, "templates")

# Base input folders
EVIDENT_PATH = get_setting("EVIDENT_PATH", "")
EVOLUTION_DROP_PATH = get_setting("EVOLUTION_DROP_PATH", r"Z:\Evolution Drop Files")
TRIOS_SCAN_ROOT = get_setting("TRIOS_SCAN_ROOT", "")
SIGNATURE_DOCTORS_PATH = get_setting("SIGNATURE_DOCTORS_PATH", _DEFAULT_SIGNATURE_DOCTORS_PATH)
TEMPLATE_DIR = get_setting("TEMPLATE_DIR", _DEFAULT_TEMPLATE_DIR)
JOTFORM_PATH = get_admin_setting("JOTFORM_PATH", os.getenv("JOTFORM_PATH", ""))

# --- Evolution internal API (direct on LAN) ---
EV_INT_BASE = get_admin_setting("EV_INT_BASE", os.getenv("EV_INT_BASE", ""))
EVO_USER = get_admin_setting("EVO_USER", os.getenv("EVO_USER", ""))
EVO_PASS = get_admin_setting("EVO_PASS", os.getenv("EVO_PASS", ""))
EVO_TIMEOUT = float(os.getenv("EVO_TIMEOUT", "15"))
EVO_VERIFY_SSL = os.getenv("EVO_VERIFY_SSL", "false").lower() == "true"

# Separate creds for the EVO image server (IIS Basic)
IMG_USER = get_admin_setting("IMG_USER", os.getenv("IMG_USER", ""))
IMG_PASS = get_admin_setting("IMG_PASS", os.getenv("IMG_PASS", ""))

# New static output structure
CC_IMPORTED_ROOT = get_setting("CC_IMPORTED_ROOT", "")

SEND_TO_AI_PATH = os.path.join(CC_IMPORTED_ROOT, "Send to AI") if CC_IMPORTED_ROOT else ""
SEND_TO_ARGEN_PATH = os.path.join(CC_IMPORTED_ROOT, "Send to Argen") if CC_IMPORTED_ROOT else ""
SEND_TO_1_9_PATH = os.path.join(CC_IMPORTED_ROOT, "Send to 1.9") if CC_IMPORTED_ROOT else ""
FAILED_IMPORT_PATH = os.path.join(CC_IMPORTED_ROOT, "Failed to import") if CC_IMPORTED_ROOT else ""

# Ensure all target folders exist only when root is configured
for path in [SEND_TO_AI_PATH, SEND_TO_ARGEN_PATH, SEND_TO_1_9_PATH, FAILED_IMPORT_PATH]:
    if path:
        os.makedirs(path, exist_ok=True)

# Debug mode toggle
DEBUG_MODE = False


def doctor_outcomes_live_enabled() -> bool:
    """
    Default off. When true, doctor_overrides YAML rules with `outcomes[]` are evaluated
    in the live template override seam (see doctor_override_runtime).

    Set env CASE_CREATOR_DOCTOR_OUTCOMES_LIVE to 1/true/yes/on to enable.
    """
    return (os.getenv("CASE_CREATOR_DOCTOR_OUTCOMES_LIVE") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )