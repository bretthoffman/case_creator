import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from case_processor_final_clean import process_case, unzip_3oxz, debug
from config import EVOLUTION_DROP_PATH, EVIDENT_PATH, FAILED_IMPORT_PATH

def extract_patient_name_from_3oxz(oxz_path, log_callback):
    extract_dir = oxz_path.rstrip(".3oxz") + "_extracted"
    unzip_3oxz(oxz_path, extract_dir)

    ox_file_path = None
    for root, dirs, files in os.walk(extract_dir):
        for f in files:
            if f.endswith(".3ox"):
                ox_file_path = os.path.join(root, f)
                break
        if ox_file_path:
            break

    if not ox_file_path:
        log_callback("❌ No .3ox file found in extracted archive.")
        return None, None

    try:
        with open(ox_file_path, "r", encoding="utf-16") as f:
            lines = f.readlines()

        debug("🔍 First 20 lines of the .3ox file:")
        for i, line in enumerate(lines[:20]):
            debug(line.strip())

        for line in lines:
            if "<Comments>" in line and "</Comments>" in line:
                comment = line.strip().split(">")[1].split("<")[0]
                debug(f"📝 Found comment: {comment}")
                parts = comment.strip().split()
                if len(parts) >= 2:
                    last, first = parts[0], parts[1]
                    drlast = parts[-1]
                    log_callback(f'Pt: {first} {last}, Dr. {drlast}')
                    return first, last

        log_callback("❌ Could not extract name from Comments tag.")
        return None, None

    except Exception as e:
        log_callback(f"❌ Failed to read or parse .3ox file: {e}")
        return None, None

def find_drop_file(case_id):
    for filename in os.listdir(EVOLUTION_DROP_PATH):
        if filename.startswith(case_id) and filename.endswith(".3oxz"):
            return os.path.join(EVOLUTION_DROP_PATH, filename)
    return None

def find_evident_folder(case_id, first_name, last_name, root_dir, log_callback):
    first = first_name.lower().strip()
    last = last_name.lower().strip()
    candidate_folders = []

    for portal in os.listdir(root_dir):
        portal_path = os.path.join(root_dir, portal)
        if not os.path.isdir(portal_path):
            continue
        for date_folder in os.listdir(portal_path):
            date_path = os.path.join(portal_path, date_folder)
            if not os.path.isdir(date_path):
                continue
            for folder in os.listdir(date_path):
                full_path = os.path.join(date_path, folder)
                if not os.path.isdir(full_path):
                    continue
                candidate_folders.append((portal, date_folder, full_path))

    candidate_folders.sort(key=lambda p: os.path.getmtime(p[2]), reverse=True)
    for portal, date, folder in candidate_folders:
        name_lower = os.path.basename(folder).lower()
        if last in name_lower and first in name_lower:
            cip_path = os.path.join(folder, "cip.csv")
            if os.path.exists(cip_path):
                log_callback(f"{portal} Case" )
                log_callback(f"📁 Found matching folder in {portal}/{date}")
                return folder

    return None

def process_case_from_id(case_id, log_callback=print):
    if not case_id:
        with open(os.path.join(FAILED_IMPORT_PATH, f"{case_id}.txt"), "w") as f:
            f.write("No case ID found\n")
        log_callback("❌ No case ID provided.")
        return

    #log_callback(f"📦 Processing case: {case_id}")
    drop_file_path = find_drop_file(case_id)

    if not drop_file_path:
        log_callback(f"❌ file not found for {case_id}")
        with open(os.path.join(FAILED_IMPORT_PATH, f"{case_id}.txt"), "w") as f:
            f.write("3oxz file not found\n")
        return

    first, last = extract_patient_name_from_3oxz(drop_file_path, log_callback)
    if not first or not last:
        log_callback(f"❌ Could not extract patient name from: {drop_file_path}")
        with open(os.path.join(FAILED_IMPORT_PATH, f"{case_id}.txt"), "w") as f:
            f.write("Could not extract patient name\n")
        return

    folder_path = find_evident_folder(case_id, first, last, EVIDENT_PATH, log_callback)
    if not folder_path:
        log_callback(f"❌ Could not find matching Evident folder for patient: {last}, {first}")
        with open(os.path.join(FAILED_IMPORT_PATH, f"{case_id}.txt"), "w") as f:
            f.write("Evident folder not found\n")
        return

    try:
        result = process_case(folder_path, log_callback)
        log_callback("✅ Scans and PDF copied over")
    except Exception as e:
        log_callback(f"❌ Failed to process {case_id}: {e}")
