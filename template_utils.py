import os
import uuid
import time
from domain.rules.doctor_rules import (
    is_abby_dew,
    is_signature_doctor,
    is_vd_brier_creek,
)
from domain.rules import template_rules


def is_non_argen_shade(shade: str) -> bool:
    return template_rules.is_non_argen_shade(shade)

def select_template(case_data):
    signature = case_data.get("signature", False)
    material = case_data.get("material", "").lower()
    has_study = case_data.get("has_study", False)
    scanner = case_data.get("scanner", "")
    shade_usable = case_data.get("shade_usable", False)
    is_itero = template_rules.is_itero_scanner(scanner)
    is_ai = case_data.get("is_ai")
    is_anterior = case_data.get("is_anterior")

    doctor_name = case_data.get("doctor", "")
    shade = case_data.get("shade", "")

    # 🎯 Special routing flags
    is_abby = is_abby_dew(doctor_name)
    non_argen_shade = is_non_argen_shade(shade)
    is_vd_serbia = is_vd_brier_creek(doctor_name)

    
    # Route family from case data (no hint-route transformation; see template_rules.effective_argen_hint_route).
    hint_route = template_rules.effective_argen_hint_route(
        template_rules.normalized_hint_route(case_data),
        material,
    )

    # 🔒 Rule: Anterior teeth cannot be sent to Argen

    if is_anterior and not has_study:
        if is_itero and template_rules.is_adz_material(material):
            folder = "itero_adzir_anterior"
        elif is_itero:
            folder = "itero_envision_anterior"
        elif template_rules.is_adz_material(material):
            folder = "reg_adzir_anterior"
        else:
            folder = "reg_envision_anterior"

    # Argen contact-model mode ON: valid Argen routes go straight to contact-model templates (not via hint rewriting).
    elif (
        template_rules.contact_model_argen_on()
        and template_rules.is_eligible_contact_model_argen_case(case_data)
        and not has_study
    ):
        folder = (
            "argen_modeless_adzir"
            if template_rules.is_adz_material(material)
            else "argen_modeless_envision"
        )

    # Modeless (Argen-only) fast path when hint is modeless and contact-model mode is off (or study path above skipped).
    elif hint_route == "modeless" and not has_study:
        folder = "argen_modeless_adzir" if template_rules.is_adz_material(material) else "argen_modeless_envision"

    elif is_ai and is_itero:
        folder = "ai_envision"

    elif is_ai and not is_itero:
        folder = "ai_envision_model"

    elif not has_study and is_itero and signature and template_rules.is_adz_material(material):
        folder = "ai_adzir"

    elif not has_study and not signature and is_itero and template_rules.is_adz_material(material) and not shade_usable:
        folder = "ai_adzir"

    elif not has_study and not signature and not is_itero and template_rules.is_adz_material(material) and not shade_usable:
        folder = "ai_adzir_model"

    elif not has_study and signature and is_itero and not template_rules.is_adz_material(material):
        folder = "ai_envision"

    elif not has_study and signature and not is_itero and not template_rules.is_adz_material(material):
        folder = "ai_envision_model"

    elif not has_study and not signature and is_itero and not template_rules.is_adz_material(material) and not shade_usable:
        folder = "ai_envision"

    elif not has_study and not signature and not is_itero and not template_rules.is_adz_material(material) and not shade_usable:
        folder = "ai_envision_model"

    elif not has_study and not signature and template_rules.is_adz_material(material) and shade_usable and not non_argen_shade and not is_abby and not is_vd_serbia:
        folder = "argen_adzir"

    elif not has_study and not signature and template_rules.is_adz_material(material) and shade_usable and non_argen_shade and is_itero:
        folder = "ai_adzir"

    elif not has_study and not signature and template_rules.is_adz_material(material) and shade_usable and non_argen_shade and not is_itero:
        folder = "ai_adzir_model"

    elif not has_study and not signature and template_rules.is_adz_material(material) and not is_itero and is_vd_serbia:
        folder = "ai_adzir_model"

    elif not has_study and not signature and template_rules.is_adz_material(material) and shade_usable and is_abby:
        folder = "ai_adzir"

    elif not has_study and not signature and not template_rules.is_adz_material(material) and shade_usable and not non_argen_shade and not is_abby and not is_vd_serbia:
        folder = "argen_envision"

    elif not has_study and not signature and not template_rules.is_adz_material(material) and shade_usable and non_argen_shade and is_itero:
        folder = "ai_envision"

    elif not has_study and not signature and not template_rules.is_adz_material(material) and shade_usable and non_argen_shade and not is_itero:
        folder = "ai_envision_model"

    elif not has_study and not signature and not template_rules.is_adz_material(material) and not is_itero and is_vd_serbia:
        folder = "ai_envision_model"

    elif not has_study and not signature and not template_rules.is_adz_material(material) and shade_usable and is_abby:
        folder = "ai_envision"

    elif is_itero and has_study and template_rules.is_adz_material(material):
        folder = "itero_adzir_study"

    elif is_itero and has_study and not template_rules.is_adz_material(material):
        folder = "itero_envision_study"
    
    elif not is_itero and has_study and template_rules.is_adz_material(material):
        folder = "reg_adzir_study"

    elif not is_itero and has_study and not template_rules.is_adz_material(material):
        folder = "reg_envision_study"

    else:
        raise ValueError("❌ Could not determine a valid template mapping for this case.")

    template_path = template_rules.build_template_path(folder)
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
