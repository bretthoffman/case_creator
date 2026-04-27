import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.append(str(_REPO_ROOT))

import uuid
import time
import pandas as pd
from config import SIGNATURE_DOCTORS_PATH, TEMPLATE_DIR

def is_signature_doctor(doctor_name: str) -> bool:
    """
    Adds 'Dr. ' prefix and checks if the name appears in the signature doctor list.
    """
    if not doctor_name:
        return False

    full_name = f"Dr. {doctor_name.strip()}"  # <- Normalize like the Excel list

    try:
        df = pd.read_excel(SIGNATURE_DOCTORS_PATH, engine="openpyxl")
        doctor_list = df["Name"].dropna().astype(str).str.strip().str.lower().tolist()
        return full_name.lower() in doctor_list
    except Exception as e:
        print(f"[ERROR] Could not read signature doctor list: {e}")
        return False

def is_abby_dew(doctor_name: str) -> bool:
    """
    True if doctor's name contains both 'abby' and 'dew' (case-insensitive).
    """
    if not doctor_name:
        return False

    name = doctor_name.lower()
    return "abby" in name and "dew" in name

def is_vd_brier_creek(doctor_name: str) -> bool:
    """
    True if doctor's name contains BOTH:
    - one of the specified last names
    - and 'vd-brier creek'
    (case-insensitive)
    """
    if not doctor_name:
        return False

    name = doctor_name.lower()

    vd_last_names = [
        "britt",
        "de frias",
        "escobar",
        "martin",
    ]

    has_last_name = any(last in name for last in vd_last_names)
    has_location = "brier creek" in name

    return has_last_name and has_location

def is_non_argen_shade(shade: str) -> bool:
    """
    True if shade indicates C3 or A4 (case-insensitive).
    """
    if not shade:
        return False

    shade_upper = shade.upper()
    return "C3" in shade_upper or "A4" in shade_upper

def select_template(case_data):
    signature = case_data.get("signature", False)
    material = case_data.get("material", "").lower()
    has_study = case_data.get("has_study", False)
    scanner = case_data.get("scanner", "")
    shade_usable = case_data.get("shade_usable", False)
    is_itero = "itero" in scanner.lower()
    is_ai = case_data.get("is_ai")
    is_anterior = case_data.get("is_anterior")

    doctor_name = case_data.get("doctor", "")
    shade = case_data.get("shade", "")

    # 🎯 Special routing flags
    is_abby = is_abby_dew(doctor_name)
    non_argen_shade = is_non_argen_shade(shade)
    is_vd_serbia = is_vd_brier_creek(doctor_name)

    
    # New: route family from evo_to_case_data for branching
    hint_route = (case_data.get("material_hint", {}).get("route") or "").lower()

    # 🔒 Rule: Anterior teeth cannot be sent to Argen

    if is_anterior and not has_study:
        if is_itero and "adz" in material:
            folder = "itero_adzir_anterior"
        elif is_itero:
            folder = "itero_envision_anterior"
        elif "adz" in material:
            folder = "reg_adzir_anterior"
        else:
            folder = "reg_envision_anterior"

    # ✅ NEW: Modeless (Argen-only) fast path
    # We only set hint_route == "modeless" in evo_to_case_data when the case is Argen AND services indicate modeless.
    elif hint_route == "modeless" and not has_study:
        folder = "argen_modeless_adzir" if "adz" in material else "argen_modeless_envision"

    elif is_ai and is_itero:
        folder = "ai_envision"

    elif is_ai and not is_itero:
        folder = "ai_envision_model"

    elif not has_study and is_itero and signature and "adz" in material:
        folder = "ai_adzir"

    elif not has_study and not signature and is_itero and "adz" in material and not shade_usable:
        folder = "ai_adzir"

    elif not has_study and not signature and not is_itero and "adz" in material and not shade_usable:
        folder = "ai_adzir_model"

    elif not has_study and signature and is_itero and not "adz" in material:
        folder = "ai_envision"

    elif not has_study and signature and not is_itero and not "adz" in material:
        folder = "ai_envision_model"

    elif not has_study and not signature and is_itero and not "adz" in material and not shade_usable:
        folder = "ai_envision"

    elif not has_study and not signature and not is_itero and not "adz" in material and not shade_usable:
        folder = "ai_envision_model"

    elif not has_study and not signature and "adz" in material and shade_usable and not non_argen_shade and not is_abby and not is_vd_serbia:
        folder = "argen_adzir"

    elif not has_study and not signature and "adz" in material and shade_usable and non_argen_shade and is_itero:
        folder = "ai_adzir"

    elif not has_study and not signature and "adz" in material and shade_usable and non_argen_shade and not is_itero:
        folder = "ai_adzir_model"

    elif not has_study and not signature and "adz" in material and not is_itero and is_vd_serbia:
        folder = "ai_adzir_model"

    elif not has_study and not signature and "adz" in material and shade_usable and is_abby:
        folder = "ai_adzir"

    elif not has_study and not signature and not "adz" in material and shade_usable and not non_argen_shade and not is_abby and not is_vd_serbia:
        folder = "argen_envision"

    elif not has_study and not signature and not "adz" in material and shade_usable and non_argen_shade and is_itero:
        folder = "ai_envision"

    elif not has_study and not signature and not "adz" in material and shade_usable and non_argen_shade and not is_itero:
        folder = "ai_envision_model"

    elif not has_study and not signature and not "adz" in material and not is_itero and is_vd_serbia:
        folder = "ai_envision_model"

    elif not has_study and not signature and not "adz" in material and shade_usable and is_abby:
        folder = "ai_envision"

    elif is_itero and has_study and "adz" in material:
        folder = "itero_adzir_study"

    elif is_itero and has_study and not "adz" in material:
        folder = "itero_envision_study"
    
    elif not is_itero and has_study and "adz" in material:
        folder = "reg_adzir_study"

    elif not is_itero and has_study and not "adz" in material:
        folder = "reg_envision_study"

    else:
        raise ValueError("❌ Could not determine a valid template mapping for this case.")

    filename = f"{folder}.xml"
    template_path = os.path.join(TEMPLATE_DIR, folder, filename)
    if is_anterior:
        print(f"[TEMPLATE] 🚫 Anterior tooth — using: {template_path}")
    else:
        print(f"[TEMPLATE] ✅ Using template: {template_path}")
    return template_path

def generate_id(prefix):
    return f"{prefix}{uuid.uuid4().hex.upper()}"

def generate_num_order_id():
    base = "643914648"
    suffix = str(int(time.time() * 1000))[-8:]
    return base + suffix

def generate_id_block():
    return {
        # Model Jobs
        "MODEL_JOB_ID_1": generate_id("MJ"),
        "MODEL_JOB_ID_2": generate_id("MJ"),

        # Model Elements
        "MODEL_ELEMENT_ID_1": generate_id("ME"),
        "MODEL_ELEMENT_ID_2": generate_id("ME"),
        "MODEL_ELEMENT_ID_3": generate_id("ME"),
        "MODEL_ELEMENT_ID_4": generate_id("ME"),
        "MODEL_ELEMENT_ID_5": generate_id("ME"),
        "MODEL_ELEMENT_ID_6": generate_id("ME"),

        # DigitalModelElementInfo IDs
        "DIGITAL_MODEL_ELEMENT_INFO_ID_1": generate_id("DM"),
        "DIGITAL_MODEL_ELEMENT_INFO_ID_2": generate_id("DM"),
        "DIGITAL_MODEL_ELEMENT_INFO_ID_3": generate_id("DM"),
        "DIGITAL_MODEL_ELEMENT_INFO_ID_4": generate_id("DM"),
        "DIGITAL_MODEL_ELEMENT_INFO_ID_5": generate_id("DM"),

        # Tooth Element
        "TOOTH_ELEMENT_ID": generate_id("TE"),

        # Custom Data
        "CUSTOM_DATA_ID_1": generate_id("CD"),
        "CUSTOM_DATA_ID_2": generate_id("CD"),
        "CUSTOM_DATA_ID_3": generate_id("CD"),
        "CUSTOM_DATA_ID_4": generate_id("CD"),
        "CUSTOM_DATA_ID_5": generate_id("CD"),
        "CUSTOM_DATA_ID_6": generate_id("CD"),

        # Scan IDs
        "SCAN_ID_1": generate_id("S"),
        "SCAN_ID_2": generate_id("S"),
        "SCAN_ID_3": generate_id("S"),

        # Order ID
        "NUM_ORDER_ID": generate_num_order_id()
    }

def map_material_to_xml(case_data):
    material = case_data.get("material", "").lower()
    has_study = case_data.get("has_study", False)

    if not has_study and "adz" in material:
        return "ArgenZ HT+ Multilayer"
    elif not has_study:
        return "ArgenZ ST Multilayer Pre-Shaded"
    elif "adz" in material:
        return "Adzir"
    else:
        return "Multi layer"
    
def inject_shade_into_materials(materials_template_path: str, destination_path: str, shade: str):
    with open(materials_template_path, 'r', encoding='utf-8') as f:
        content = f.read()

    content = content.replace("{{SHADE}}", shade)

    with open(destination_path, 'w', encoding='utf-8') as f:
        f.write(content)
