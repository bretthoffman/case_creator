import os, zipfile, re, shutil, csv, json, uuid, time
import xml.etree.ElementTree as ET
from datetime import datetime
from template_utils import (
    generate_id_block, map_material_to_xml, is_signature_doctor, inject_shade_into_materials
)

# 🔗 Evo (API-mode)
from evo_internal_client import get_case_detail_clean
from evo_to_case_data import build_case_data_from_evo
from domain.decisions.manual_review_selector import (
    evaluate_initial_manual_review,
    evaluate_jotform_manual_review,
)
from domain.decisions.destination_selector import select_destination
from domain.decisions.template_selector import select_template_path
from domain.rules import routing_rules, naming_rules
# 📦 Paths & flags
from config import (
    DEBUG_MODE,
    EVOLUTION_DROP_PATH,     # keep if still used elsewhere
    SEND_TO_AI_PATH,
    SEND_TO_ARGEN_PATH,
    SEND_TO_1_9_PATH,
    FAILED_IMPORT_PATH,
)

STUDY_SCAN_KEYWORDS = [
    "preprep", "pre-prep", "pre-op", "preop", "pretreat", "pre_treat", "pre-treat", "pretreatment", "situ", "study", "pre-scan", "pre_scan"
]

SCAN_KEYWORDS = {
    "prep": "Raw Preparation scan",
    "antagonist": "Raw Antagonist scan",
    "study": "PrePreparationScan"
}

def debug(msg):
    if DEBUG_MODE:
        print(f"[DEBUG] {msg}")


def zip_case_folder(folder_path: str, log_callback=lambda *_: None) -> str:
    """
    Zips `folder_path` so the .zip contains the folder itself as the top-level entry.
    Returns the full path to the created .zip.
    """
    parent = os.path.dirname(folder_path)
    base   = os.path.basename(folder_path)
    zip_base = os.path.join(parent, base)  # shutil adds .zip

    # replace any existing zip with same name
    if os.path.exists(zip_base + ".zip"):
        try:
            os.remove(zip_base + ".zip")
        except Exception as e:
            log_callback(f"⚠️ Could not remove existing zip: {e}")

    # Important: root_dir=parent, base_dir=folder-name -> zip will contain the folder
    shutil.make_archive(zip_base, "zip", root_dir=parent, base_dir=base)
    zip_path = zip_base + ".zip"
    log_callback(f"📦 Created zip: {zip_path}")
    return zip_path

def should_zip(case_data, template_path, target_root) -> bool:
    """
    Only zip when:
      - case is the 'modeless' family (Argen-only per evo_to_case_data), AND
      - the chosen template is an Argen template (or target_root is Argen path).
    """
    destination_key = (
        routing_rules.DEST_ARGEN
        if target_root == SEND_TO_ARGEN_PATH
        else routing_rules.DEST_1_9
    )
    return routing_rules.should_zip_modeless_argen(case_data, template_path, destination_key)


def is_case_in_jotform(firstname, lastname):
    from config import JOTFORM_PATH
    formatted_first = firstname.strip().upper()
    formatted_last = lastname.strip().upper()
    for root, dirs, _ in os.walk(JOTFORM_PATH):
        for d in dirs:
            name = d.upper()
            if formatted_first in name and formatted_last in name:
                return True
    return False

def replace_id(prop, prefix):
    prop.set("value", prefix + uuid.uuid4().hex.upper())


def rename_scans(folder_path, arch, tooth=None, scanner=""):
    debug(f"Renaming scan files using arch={arch}, tooth={tooth}, scanner={scanner}...")
    found_study = False

    # 🧪 Create a safe isolated scan folder
    temp_work_folder = os.path.join(folder_path, "_scan_processing")
    if os.path.exists(temp_work_folder):
        shutil.rmtree(temp_work_folder)
    os.makedirs(temp_work_folder, exist_ok=True)

    # ✅ Locate Sirona nested scan folder (read-only)
    scan_input_folder = folder_path
    scanner_temp = (scanner or "").lower()
    if "sirona" in scanner_temp:
        debug("🔍 Looking for nested scan folder (Sirona case)")
        subfolders = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]
        # If we know patient name, we could bias, but keep generic in API-mode:
        for f in subfolders:
            cand = os.path.join(folder_path, f)
            # choose the first subfolder that actually has STLs
            if any(x.lower().endswith(".stl") for x in os.listdir(cand)):
                scan_input_folder = cand
                debug(f"✅ Sirona nested folder found: {scan_input_folder}")
                break

    # ✅ Copy only .stl scan files into isolated working folder
        # ✅ Copy .stl scan files into isolated working folder (RECURSIVE)
    stl_found = 0
    for root, _, files in os.walk(scan_input_folder):
        for f in files:
            if f.lower().endswith(".stl"):
                src = os.path.join(root, f)
                dst = os.path.join(temp_work_folder, f)
                try:
                    shutil.copy2(src, dst)
                    stl_found += 1
                except Exception as e:
                    debug(f"⚠️ Could not copy STL '{src}': {e}")

    debug(f"[stl-scan] Collected {stl_found} STL(s) from '{scan_input_folder}'")


    if not tooth:
        debug("⚠️ No tooth number provided. Cannot proceed with scan naming.")
        raise FileNotFoundError("Missing tooth number")


    try:
        tooth_num = int(tooth)
        is_upper = 1 <= tooth_num <= 16
    except Exception as e:
        debug(f"❌ Invalid tooth number: {e}")
        raise FileNotFoundError("Invalid tooth number")


    scan_files = [f for f in os.listdir(temp_work_folder) if f.lower().endswith(".stl")]
    categorized = {"upper": [], "lower": [], "study": []}
    unused = []

    UPPER_KEYWORDS = ["upper", "max", "maxillary", "occlusion_u"]
    LOWER_KEYWORDS = ["lower", "mand", "mandibular", "occlusion_l", "antagonist", "opposing"]
    PREP_KEYWORDS = ["prep", "preparation", "raw preparation"]
    ANTAG_KEYWORDS = ["antagonist", "opposing", "raw antagonist"]

    for f in scan_files:
        name = f.lower()
        if any(k in name for k in STUDY_SCAN_KEYWORDS):
            categorized["study"].append(f)
        elif any(k in name for k in UPPER_KEYWORDS):
            categorized["upper"].append(f)
        elif any(k in name for k in LOWER_KEYWORDS):
            categorized["lower"].append(f)
        elif any(k in name for k in PREP_KEYWORDS + ANTAG_KEYWORDS):
            categorized["ambiguous"] = categorized.get("ambiguous", []) + [f]
        else:
            unused.append(f)

    if "ambiguous" in categorized:
        ambigs = categorized["ambiguous"]
        del categorized["ambiguous"]

        for f in ambigs:
            name = f.lower()

            if any(k in name for k in STUDY_SCAN_KEYWORDS):
                categorized["study"].append(f)
                debug(f"🚫 Prevented misclassification: {f} reassigned to 'study'")
                continue

            if any(k in name for k in PREP_KEYWORDS):
                if is_upper:
                    categorized["upper"].append(f)
                else:
                    categorized["lower"].append(f)
                debug(f"🔀 Fallback assigned {f} to {'upper' if is_upper else 'lower'} as prep")
            elif any(k in name for k in ANTAG_KEYWORDS):
                if is_upper:
                    categorized["lower"].append(f)
                else:
                    categorized["upper"].append(f)
                debug(f"🔀 Fallback assigned {f} to {'lower' if is_upper else 'upper'} as antagonist")
            else:
                unused.append(f)

    def choose_best(files):
        if not files:
            return None
        without = [f for f in files if "without_ditch" in f.lower()]
        if without:
            return without[0]
        return files[0]

    arch_folder = f"{'UNN' if is_upper else 'LNN'}{str(tooth_num).zfill(2)}"
    scan_dir = os.path.join(temp_work_folder, "Scans", arch_folder)
    os.makedirs(scan_dir, exist_ok=True)

    prep_found = False

    prep_candidate = choose_best(categorized["upper"] if is_upper else categorized["lower"])
    if prep_candidate:
        src = os.path.join(temp_work_folder, prep_candidate)
        dst = os.path.join(scan_dir, "PreparationScan.stl")
        shutil.copy2(src, dst)
        debug(f"🦷 PreparationScan → {prep_candidate}")
        prep_found = True

    ant_candidate = choose_best(categorized["lower"] if is_upper else categorized["upper"])
    if ant_candidate:
        src = os.path.join(temp_work_folder, ant_candidate)
        dst = os.path.join(scan_dir, "AntagonistScan.stl")
        shutil.copy2(src, dst)
        debug(f"🦷 AntagonistScan → {ant_candidate}")

    study_candidate = choose_best(categorized["study"])
    if study_candidate:
        src = os.path.join(temp_work_folder, study_candidate)
        dst = os.path.join(scan_dir, "PrePreparationScan.stl")
        shutil.copy2(src, dst)
        debug(f"🧪 PrePreparationScan → {study_candidate}")
        found_study = True

    # 👇 Add this block here
    if not prep_found:
        debug(f"[categorize] upper={categorized['upper']}, lower={categorized['lower']}, study={categorized['study']}")
        debug("⚠️ No preparation scan found — case may fail to load in preview")

    if unused:
        debug("🗃 Unused scans:")
        for name in unused:
            debug(f" - {name}")

    # ✅ Let caller access the isolated folder path
    return found_study, scan_dir


def process_case(case_number, folder_path, log_callback=print):
    debug(f"Starting case processing for folder: {folder_path}")
    final_output = None
    scan_source_folder = folder_path
    renamed_scan_dir = None
    case_id = str(case_number)  # initialize early for error paths

    try:
        # 🔎 Pull case data from Evolution API
        clean = get_case_detail_clean(case_number)
        case_data = build_case_data_from_evo(clean)
        initial_review = evaluate_initial_manual_review(clean, case_data)
        if initial_review.requires_manual_review:
            if initial_review.message:
                log_callback(initial_review.message)
            if initial_review.detail:
                log_callback(initial_review.detail)
            return initial_review.return_value or initial_review.message

        route = (case_data.get("material_hint", {}).get("route") or "").lower()

        # --- begin: populate fields used by template_utils.select_template ---
        # 1) material: ADZ vs Envision
        if route == "modeless":
            # Use the material computed upstream in evo_to_case_data (from service descriptions)
            mat = (case_data.get("material_hint", {}).get("material") or "").lower()
            case_data["material"] = "adz" if mat == "adz" else "envision"
            log_callback("🧱 MODELESS CASE (Argen)")
        else:
            # Legacy behavior for non-modeless routes
            case_data["material"] = "adz" if any(k in route for k in ("adz", "adzir", "argenz")) else "envision"
        # --- end: populate fields used by template_utils.select_template ---


        # 2) shade_usable: true if a shade string exists
        case_data["shade_usable"] = bool((case_data.get("shade") or "").strip())

        # 3) signature: use your helper
        from template_utils import is_signature_doctor
        case_data["signature"] = is_signature_doctor(case_data.get("doctor", ""))

        # 4) scanner: infer from folder name when Evolution doesn't specify
        fp_lower = (folder_path or "").lower()
        s = (case_data.get("scanner") or "").lower()
        if not s:
            if "3shape" in fp_lower:
                s = "3shape"
            elif "itero" in fp_lower:
                s = "itero"
            elif "sirona" in fp_lower:
                s = "sirona"
        case_data["scanner"] = s
        # --- end: populate fields used by template_utils.select_template ---

        case_id = case_data.get("case_id") or case_id

        log_callback(f"📦 Starting import: {case_id}")
        log_callback(f"Pt: {case_data.get('first','')} {case_data.get('last','')}, Dr. {case_data.get('doctor','')}")
        log_callback(f"🦷 Tooth = {case_data.get('tooth', 'unknown')}")

        if case_data.get("signature"):
            print("🎯 SIGNATURE DOCTOR")
            log_callback("👤 SIGNATURE DR")

        scanner = case_data.get("scanner", "").lower()
        # --- begin: infer scanner from folder path as fallback ---
        fp_lower = (folder_path or "").lower()
        if "3shape" in fp_lower:
            scanner = "3shape"
        elif "itero" in fp_lower:
            scanner = "itero"
        case_data["scanner"] = scanner
        debug(f"[scanner-detect] Using scanner='{scanner}' (folder inference)")
        # --- end: infer scanner from folder path as fallback ---

        debug(f"Scanner = {scanner}")
        scan_source_folder = folder_path  # default
        first = case_data.get("first", "").strip().replace(" ", "_")
        last = case_data.get("last", "").strip().replace(" ", "_")
        if "3shape" in scanner:
            debug("Connecting to 3shape scans")
            from config import TRIOS_SCAN_ROOT

            # Build canonical base names (apostrophes/spaces already normalized above)
            last_clean = last.replace("'", "_").replace(" ", "_")
            first_clean = first.replace("'", "_").replace(" ", "_")
            base_name = f"{last_clean}_{first_clean}"
            alt_name = f"{last_clean}__{first_clean}"  # double-underscore fallback

            # Pattern to match: base, base(1), base(2) ... (case-insensitive)
            # We’ll check both single-underscore and double-underscore families.
            def build_regex(name):
                return re.compile(rf"^{re.escape(name)}(?:\(\d+\))?$", re.IGNORECASE)

            pat_base = build_regex(base_name)
            pat_alt  = build_regex(alt_name)

            # Collect all candidate patient folders under TRIOS_SCAN_ROOT
            candidates = []
            try:
                for entry in os.listdir(TRIOS_SCAN_ROOT):
                    full = os.path.join(TRIOS_SCAN_ROOT, entry)
                    if not os.path.isdir(full):
                        continue
                    if pat_base.match(entry) or pat_alt.match(entry):
                        scans_path = os.path.join(full, "Scans")
                        if os.path.isdir(scans_path):
                            try:
                                mtime = os.path.getmtime(full)
                            except Exception:
                                mtime = 0
                            candidates.append((mtime, scans_path, full, entry))
            except FileNotFoundError:
                pass

            if not candidates:
                # Maintain your helpful error with the exact tried bases
                raise FileNotFoundError(
                    f"❌ Expected 3Shape scan folder not found. "
                    f"Tried families under {TRIOS_SCAN_ROOT}: {base_name}, {alt_name} (including numbered siblings like (1), (2))"
                )

            # Pick newest folder by modified time
            candidates.sort(key=lambda t: t[0], reverse=True)
            newest_mtime, scans_path, full_patient_path, folder_name = candidates[0]

            scan_source_folder = scans_path
            debug(f"✅ Selected 3Shape folder: {full_patient_path} → Scans (newest by mtime)")

            # Study-detection (unchanged logic)
            study_found = False
            for root, _, files in os.walk(scan_source_folder):
                for f in files:
                    if any(keyword in f.lower() for keyword in STUDY_SCAN_KEYWORDS):
                        study_found = True
                        break
                if study_found:
                    break

            if study_found:
                print("HAS A STUDY (3Shape direct scan check)")
                log_callback("🖋 HAS A STUDY")
            else:
                print("NO STUDY AVAILABLE (3Shape direct scan check)")
                log_callback("❌ NO STUDY AVAILABLE")

        case_id = case_data.get("case_id")
        if not case_id:
            raise ValueError("Case ID missing from Evolution response")

        
        # Determine output folder from template name

        # --- begin: iTero nested scans support (choose unzipped child folder with STLs) ---
        if "itero" in scanner:
            parent_name = os.path.basename(folder_path).strip()
            subdirs = [d for d in os.listdir(folder_path)
                       if os.path.isdir(os.path.join(folder_path, d))]
        
            def has_stls(path):
                try:
                    return any(f.lower().endswith(".stl") for f in os.listdir(path))
                except Exception:
                    return False
        
            def score(path, name):
                # Prefer: (1) name includes case_id, (2) exact parent-name match,
                # then (3) more STL files
                s = 0
                if case_id and case_id in name:
                    s += 3
                if parent_name.lower() == name.lower():
                    s += 2
                try:
                    s += sum(1 for f in os.listdir(path) if f.lower().endswith(".stl"))
                except Exception:
                    pass
                return s
        
            best = None
            for d in subdirs:
                p = os.path.join(folder_path, d)
                if has_stls(p):  # ignore zipped files; only real folders with STLs
                    sc = score(p, d)
                    if best is None or sc > best[0]:
                        best = (sc, p)
        
            if best:
                scan_source_folder = best[1]
                debug(f"✅ Found iTero nested scan folder: {scan_source_folder}")
            else:
                debug("ℹ️ No nested iTero folder with STLs found; using parent folder for scans")
        # --- end: iTero nested scans support ---

        # Rename scan files
        if not '3shape' in scanner:
            try:
                case_data["has_study"], renamed_scan_dir = rename_scans(
                    scan_source_folder,
                    case_data.get("arch", "Upper"),
                    case_data.get("tooth"),
                    case_data.get("scanner", "")
                )

                log_callback("🧪 HAS A STUDY" if case_data["has_study"] else "❌ NO STUDY AVAILABLE")
            except FileNotFoundError as scan_err:
                first = case_data.get("first", "")
                last = case_data.get("last", "")
                jotform_review = evaluate_jotform_manual_review(first, last, is_case_in_jotform)
                if jotform_review.requires_manual_review:
                    if jotform_review.message:
                        log_callback(jotform_review.message)
                    return jotform_review.return_value or jotform_review.message
                else:
                    raise scan_err  # bubble up original error if not in Jotform

            
        else:
            # For 3Shape, check if PrePreparationScan.dcm exists in either arch
            upper_study = os.path.exists(os.path.join(scan_source_folder, "Upper", "PrePreparationScan.dcm"))
            lower_study = os.path.exists(os.path.join(scan_source_folder, "Lower", "PrePreparationScan.dcm"))
            case_data["has_study"] = upper_study or lower_study
            print("HAS A STUDY" if case_data["has_study"] else "NO STUDY AVAILABLE")

        template_path = select_template_path(case_data)
        if "anterior" in template_path:
            log_callback("ANTERIOR")
        log_callback(f"📄 Using template: {os.path.basename(template_path)}")
        template_filename = routing_rules.template_filename(template_path)
        scanner = case_data.get("scanner", "").lower()
        naming_decision = naming_rules.build_case_naming(case_id, template_filename, scanner)
        if naming_decision.suffix:
            case_id = naming_decision.final_case_id
            case_data["case_id"] = case_id
        destination_decision = select_destination(template_filename, case_data.get("doctor", ""))
        if destination_decision.destination_key == routing_rules.DEST_ARGEN:
            target_root = SEND_TO_ARGEN_PATH
        elif destination_decision.destination_key == routing_rules.DEST_1_9:
            target_root = SEND_TO_1_9_PATH
            if destination_decision.is_ai_alias_to_designer:
                debug("[route] AI template re-routed to DESIGNER path")

        # Decide zipping once, based on both modeless family and Argen route
        do_zip = should_zip(case_data, template_path, target_root)
        route_label = destination_decision.route_label_key

        if route_label == routing_rules.LABEL_ARGEN:
            log_callback("🏭 ARGEN CASE")
        elif route_label == routing_rules.LABEL_DESIGNER:
            log_callback("🧑‍🎓 DESIGNER CASE")
        elif route_label == routing_rules.LABEL_SERBIA:
            log_callback("🧑‍🎓 SERBIA CASE")
        elif route_label == routing_rules.LABEL_AI_DESIGNER:
            log_callback("🤖 DESIGNER CASE")
        elif route_label == routing_rules.LABEL_AI_SERBIA:
            log_callback("🤖 SERBIA CASE")


        final_output = os.path.join(target_root, case_id)
        os.makedirs(final_output, exist_ok=True)

        # Generate XML
        final_xml_path = os.path.join(final_output, f"{case_id}.xml")
        template_dir_used = generate_final_xml(case_data, final_xml_path)

        debug(f"✅ OrderExchange-style XML saved to {final_xml_path}")

        


        # Verify preparation scan presence
        arch_dbg = case_data.get("arch", "")
        print(f"{arch_dbg} Working")

        if not '3shape' in scanner:
            required_scan_path = os.path.join(renamed_scan_dir, "PreparationScan.stl")
            if not os.path.exists(required_scan_path):
                raise FileNotFoundError(f"Missing required preparation scan for arch {case_data.get('arch')} at {required_scan_path}")

        # Copy Materials.xml and Manufacturers.3ml from template directory
        for extra in ["Materials.xml", "Manufacturers.3ml"]:
            extra_src = os.path.join(template_dir_used, extra)
            extra_dst = os.path.join(final_output, extra)
        
            if os.path.exists(extra_src):
                if extra == "Materials.xml" and "argen" in template_filename and case_data.get("shade"):
                    inject_shade_into_materials(extra_src, extra_dst, case_data["shade"])
                    debug(f"🔧 Injected shade into Materials.xml: {case_data['shade']}")
                else:
                    shutil.copy2(extra_src, extra_dst)
                    debug(f"📄 Copied {extra} to output folder")


        # ✅ Copy a readable Rx PDF for reference
        try:
            first = case_data.get("first", "").strip().replace(" ", "_")
            last = case_data.get("last", "").strip().replace(" ", "_")
            pdf_filename = None

            for f in os.listdir(folder_path):
                if f.lower().endswith(".pdf") and last.lower() in f.lower():
                    pdf_filename = f
                    break
                
            if pdf_filename:
                src = os.path.join(folder_path, pdf_filename)
                dst_filename = f"{first} {last}.pdf"
                dst = os.path.join(final_output, dst_filename)
                shutil.copy2(src, dst)
                debug(f"📄 Copied Rx PDF to output: {dst}")
        except Exception as e:
            debug(f"⚠️ Could not copy Rx PDF: {e}")


        # Copy renamed scans to 3Shape structure
        if not '3shape' in scanner:
            scan_base = os.path.dirname(renamed_scan_dir)  # one level above the arch folder
            upper_folder = os.path.join(final_output, "Scans", "Upper")
            lower_folder = os.path.join(final_output, "Scans", "Lower")
            os.makedirs(upper_folder, exist_ok=True)
            os.makedirs(lower_folder, exist_ok=True)

            if os.path.exists(scan_base):
                for arch_dir in os.listdir(scan_base):
                    arch_path = os.path.join(scan_base, arch_dir)
                    for scan_file in os.listdir(arch_path):
                        src = os.path.join(arch_path, scan_file)

                        try:
                            tooth_num = int(case_data.get("tooth", 0))
                            is_upper_case = 1 <= tooth_num <= 16
                        except Exception:
                            is_upper_case = True  # Fallback

                        dst_folder = None
                        dst_filename = None

                        if scan_file == "PreparationScan.stl":
                            dst_folder = upper_folder if is_upper_case else lower_folder
                            dst_filename = "Raw Preparation scan.stl"
                        elif scan_file == "AntagonistScan.stl":
                            dst_folder = lower_folder if is_upper_case else upper_folder
                            dst_filename = "Raw Antagonist scan.stl"
                        elif scan_file == "PrePreparationScan.stl":
                            dst_folder = upper_folder if is_upper_case else lower_folder
                            dst_filename = "PrePreparationScan.stl"
                        else:
                            debug(f"🧐 Ignored unrecognized scan during copy: {scan_file}")
                            continue

                        if dst_folder:
                            os.makedirs(dst_folder, exist_ok=True)
                            dst = os.path.join(dst_folder, dst_filename)
                            shutil.copy2(src, dst)
                            debug(f"📄 Copied scan to output: {dst}")
                        # --- ZIP FOR MODELESS CASES ---
            if do_zip:
                zip_path = zip_case_folder(final_output, log_callback)
                try:
                    shutil.rmtree(final_output)
                    log_callback(f"🧹 Removed unzipped folder: {final_output}")
                except Exception as e:
                    log_callback(f"⚠️ Failed to remove unzipped folder: {e}")
                return f"Completed {case_id} → {zip_path}"

            # --- END ZIP FOR MODELESS CASES ---

            return f"Completed {case_id} → {final_output}"

            
        else:
            # For 3Shape: directly copy Scans folder as-is
            final_scans_path = os.path.join(final_output, "Scans")
            shutil.copytree(scan_source_folder, final_scans_path, dirs_exist_ok=True)
            debug(f"🧾 Copied 3Shape scans directly to output: {final_scans_path}")
                        # --- ZIP FOR MODELESS CASES ---
            if do_zip:
                zip_path = zip_case_folder(final_output, log_callback)
                try:
                    shutil.rmtree(final_output)
                    log_callback(f"🧹 Removed unzipped folder: {final_output}")
                except Exception as e:
                    log_callback(f"⚠️ Failed to remove unzipped folder: {e}")
                return f"Completed {case_id} → {zip_path}"

            # --- END ZIP FOR MODELESS CASES ---

            return f"Completed {case_id} → {final_output}"

    except Exception as e:
        debug(f"❌ Error encountered: {e}")
        try:
            placeholder_path = os.path.join(FAILED_IMPORT_PATH, f"{case_id}.txt")
            with open(placeholder_path, "w") as f:
                f.write(f"Case {case_id} failed to import.\nError: {str(e)}\n")

            debug(f"⚠️ Case {case_id} marked as failed: {placeholder_path}")
        except:
            debug("⚠️ Failed to log case to Failed to import folder")

        raise e
    finally:
        # 🧹 Always clean up temp scan folder (success or fail)
        cleanup_path = os.path.join(scan_source_folder, "_scan_processing")
        if os.path.exists(cleanup_path):
            shutil.rmtree(cleanup_path)
            debug(f"🧼 Force-removed temp scan folder: {cleanup_path}")

# ---- Compatibility wrapper for the GUI ----
# ---- Compatibility wrapper for the GUI (2-arg form) ----
# ---- Compatibility wrapper for the GUI (2-arg form) ----
def process_case_from_id(case_id, log_callback=print):
    """
    GUI entrypoint. Finds the correct Evident folder for this case and delegates to process_case().
    New behavior: search Evident by patient FIRST+LAST (from Evolution API) inside portal/date folders,
    because iTero folders land before case numbers exist.
    Fallback: if name-based search fails, try old "folder startswith case_id".
    """
    from config import EVIDENT_PATH  # base input root(s)

    if not case_id:
        raise FileNotFoundError("Missing case id")

    # 1) Ask Evolution for patient name
    try:
        clean = get_case_detail_clean(case_id)
        cd = build_case_data_from_evo(clean)  # has 'first' and 'last'
        first = (cd.get("first") or "").strip()
        last  = (cd.get("last") or "").strip()
    except Exception as e:
        first = last = ""
        debug(f"⚠️ EVO name lookup failed for {case_id}: {e}")

    # 2) Helper: newest-first walk of portal/date folders matching FIRST & LAST
    def find_evident_folder_by_name(root_dir, first_name, last_name):
        if not first_name or not last_name:
            return None

        f = first_name.lower().replace(" ", "_")
        l = last_name.lower().replace(" ", "_")

        candidates = []
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
                    candidates.append((portal, date_folder, full_path))

        # newest first
        candidates.sort(key=lambda t: os.path.getmtime(t[2]), reverse=True)

        for portal, date_folder, full_path in candidates:
            name_lower = os.path.basename(full_path).lower()
            if (l in name_lower) and (f in name_lower):
                # Nice logging like your previous flow
                if "itero" in portal.lower():
                    log_callback("Itero Case")
                log_callback(f"📁 Found matching folder in {portal}/{date_folder}")
                return full_path

        # --- 2) Fallback for multi-part / middle names / parentheses ---
        # Only trigger if there are >2 "words" in the combined name like:
        #   "Thomas William White", "Thomas (William) White", etc.
        full_name = f"{first_name} {last_name}"
        # Keep only alphabetic chunks so things like (William) or "William"
        # still become 'william'
        tokens = re.findall(r"[a-zA-Z]+", full_name.lower())

        if len(tokens) > 2:
            simple_first = tokens[0]      # e.g. 'thomas'
            simple_last  = tokens[-1]     # e.g. 'white'

            for portal, date_folder, full_path in candidates:
                name_lower = os.path.basename(full_path).lower()
                if (simple_last in name_lower) and (simple_first in name_lower):
                    if "itero" in portal.lower():
                        log_callback("Itero Case (fallback)")
                    log_callback(f"📁 (fallback) Found matching folder in {portal}/{date_folder}")
                    return full_path

        # Nothing found

        return None

    # 3) Prefer name-based search (Itero lands before number assignment)
    found_path = find_evident_folder_by_name(EVIDENT_PATH, first, last)

    # 4) Fallback: look for a folder that equals/starts with the case number (legacy behavior)
    if not found_path:
        direct = os.path.join(EVIDENT_PATH, case_id)
        if os.path.isdir(direct):
            found_path = direct
        else:
            for root, dirs, _ in os.walk(EVIDENT_PATH):
                for d in dirs:
                    nm = d.strip()
                    if nm == case_id or nm.startswith(case_id):
                        found_path = os.path.join(root, d)
                        break
                if found_path:
                    break

    if not found_path:
        raise FileNotFoundError(f"Case folder not found under {EVIDENT_PATH} for {case_id} "
                                f"(looked by name {'/'.join([last, first]) or 'n/a'} and by number).")

    # 5) Delegate to the main processor; it already handles nested iTero scan subfolders
    return process_case(case_id, found_path, log_callback)



def generate_final_xml(case_data, output_path):
    # 1. Select base template path based on material and study presence
    template_path = select_template_path(case_data)
    print(f"[INFO] Using template: {os.path.basename(template_path)}")

    # 2. Load template content
    with open(template_path, 'r', encoding='utf-8') as f:
        xml_content = f.read()

    # 3. Generate unique IDs
    id_block = generate_id_block()
    # 3.5 Generate TOOTH_MODEL_ID
    try:
        tooth_num = int(case_data.get("tooth", 0))
        id_block["TOOTH_MODEL_ID"] = "1" if 1 <= tooth_num <= 16 else "17"
    except Exception:
        id_block["TOOTH_MODEL_ID"] = "1"  # Fallback default


    # 4. Generate timestamps
    create_ts = int(time.time())
    try:
        due_str = case_data.get("due_date", "")
        due_dt = datetime.fromisoformat(due_str)
        deliver_ts = int(due_dt.timestamp())
        if deliver_ts < create_ts:
            deliver_ts = create_ts
    except Exception:
        deliver_ts = create_ts  # fallback if parsing fails

    case_data["CREATE_DATE"] = str(create_ts)
    case_data["DELIVER_DATE"] = str(deliver_ts)

    # 5. Build substitution map
    raw_shade = case_data.get("shade", "") or ""
    # Strip a leading "Vita Classic-" (case-insensitive; tolerates spaces/colons/dashes)
    shade_clean = re.sub(r'^\s*vita\s*classic\s*[-:\s]*', '', raw_shade, flags=re.IGNORECASE).strip()
    case_data["shade"] = shade_clean   # <-- NEW: persist normalized shade for Materials.xml injection

    # --- FIX 2: sanitize OrderComments for XML attribute safety ---
    # 1) Replace all '&' with 'and' (already requested/working).
    # 2) Remove any quotes (straight or “smart”) that can break attribute parsing.
    raw_comments = case_data.get("OrderComments", "") or ""
    safe_comments = (
        raw_comments
        .replace("&", "and")
        # remove straight quotes
        .replace('"', "").replace("'", "")
        # remove common smart quotes just in case
        .replace("“", "").replace("”", "").replace("‘", "").replace("’", "")
        # optional: collapse any extra spaces created by removals
        .strip()
    )

    substitutions = {
        "CASE_ID": case_data["case_id"],
        "TOOTH_NUM": str(case_data["tooth"]),
        "SHADE": shade_clean,
        "CREATE_DATE": case_data["CREATE_DATE"],
        "DELIVER_DATE": case_data["DELIVER_DATE"],
        "NUM_ORDER_ID": id_block["NUM_ORDER_ID"],
        "ORDER_COMMENTS": safe_comments,
        **id_block
    }


    # 6. Material substitution
    material_value = map_material_to_xml(case_data)
    if case_data.get("has_study"):
        substitutions["MATERIAL"] = material_value
    else:
        substitutions["ARGEN_MATERIAL"] = material_value

    # 7. Replace placeholders
    def substitute(match):
        key = match.group(1)
        return substitutions.get(key, f"[MISSING:{key}]")

    final_xml = re.sub(r"\{\{([A-Z0-9_]+)\}\}", substitute, xml_content)

    # 8. Write output
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_xml)
        print(f"[✅] Final XML written to {output_path}")

    return os.path.dirname(template_path)