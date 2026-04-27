from case_processor_final_clean import process_case_from_id as _process_case_from_id


def import_case_by_id(case_id, log_callback=print):
    """
    Thin service wrapper over the frozen backend entrypoint.
    """
    return _process_case_from_id(case_id, log_callback)


def validate_case_id(case_id):
    """
    Conservative validation.
    Keeps behavior permissive to avoid changing current runtime behavior.
    """
    case_id_text = str(case_id).strip() if case_id is not None else ""
    return bool(case_id_text)


def build_case_id(year, case_number):
    """
    Mirrors current UI behavior exactly:
    case_number is stripped, then concatenated as f"{year}-{case_number}".
    """
    case_number_text = str(case_number).strip() if case_number is not None else ""
    return f"{year}-{case_number_text}"


def get_app_info():
    """
    Placeholder app metadata for future UI layers.
    """
    return {
        "app_name": "3Shape Case Importer",
        "app_version": "0.0.0",
    }
