import pandas as pd

from config import SIGNATURE_DOCTORS_PATH


def is_signature_doctor(doctor_name: str) -> bool:
    """
    Adds 'Dr. ' prefix and checks if the name appears in the signature doctor list.
    """
    if not doctor_name:
        return False

    full_name = f"Dr. {doctor_name.strip()}"

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
