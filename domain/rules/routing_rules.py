import os

DEST_ARGEN = "argen"
DEST_1_9 = "1_9"

LABEL_ARGEN = "argen"
LABEL_DESIGNER = "designer"
LABEL_SERBIA = "serbia"
LABEL_AI_DESIGNER = "ai_designer"
LABEL_AI_SERBIA = "ai_serbia"


def template_filename(template_path: str) -> str:
    return os.path.basename(template_path).lower()


def is_argen_template(template_path_or_name: str) -> bool:
    name = os.path.basename(template_path_or_name).lower()
    return "argen" in name


def is_study_template(template_path_or_name: str) -> bool:
    name = os.path.basename(template_path_or_name).lower()
    return "study" in name


def is_anterior_template(template_path_or_name: str) -> bool:
    name = os.path.basename(template_path_or_name).lower()
    return "anterior" in name


def is_ai_template(template_path_or_name: str) -> bool:
    name = os.path.basename(template_path_or_name).lower()
    return "ai" in name


def destination_key_for_template(template_path_or_name: str) -> str:
    """
    Preserve current runtime mapping semantics from processor:
    - argen -> argen destination
    - study/anterior/ai -> 1.9 destination
    """
    name = os.path.basename(template_path_or_name).lower()
    if "argen" in name:
        return DEST_ARGEN
    if "study" in name:
        return DEST_1_9
    if "anterior" in name:
        return DEST_1_9
    if "ai" in name:
        return DEST_1_9
    raise ValueError(f"Unrecognized template route: {name}")


def is_serbia_case(doctor_name: str) -> bool:
    return "brier creek" in (doctor_name or "").lower()


def route_label_for_template(template_path_or_name: str, doctor_name: str) -> str:
    """
    Preserve current label semantics:
    - argen templates -> ARGEN label
    - study/anterior -> designer vs serbia by doctor
    - ai -> ai_designer vs ai_serbia by doctor
    """
    name = os.path.basename(template_path_or_name).lower()
    serbia = is_serbia_case(doctor_name)
    if "argen" in name:
        return LABEL_ARGEN
    if "study" in name:
        return LABEL_SERBIA if serbia else LABEL_DESIGNER
    if "anterior" in name:
        return LABEL_SERBIA if serbia else LABEL_DESIGNER
    if "ai" in name:
        return LABEL_AI_SERBIA if serbia else LABEL_AI_DESIGNER
    raise ValueError(f"Unrecognized template route for label: {name}")


def should_zip_modeless_argen(case_data, template_path: str, destination_key: str) -> bool:
    """
    Preserve current zip policy:
    - route family == modeless
    - and template is argen OR destination is argen
    """
    route = (case_data.get("material_hint", {}).get("route") or "").lower()
    is_modeless_family = route == "modeless"
    tpl_is_argen = is_argen_template(template_path)
    is_argen_dest = destination_key == DEST_ARGEN
    return is_modeless_family and (tpl_is_argen or is_argen_dest)
