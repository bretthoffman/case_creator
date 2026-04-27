# evolution_case_detail.py
# Parser for Evolution "get_case_detail" XML → organized JSON

from __future__ import annotations
import re
import html
import datetime as dt
from typing import Any, Dict, List, Optional
import xml.etree.ElementTree as ET

# ---------------------------
# Helpers
# ---------------------------

def _extract_xml(response_text: str) -> str:
    """
    Accepts strings like 'Status: 200 Response: <response ...>...</response>'
    and returns just the '<response>...</response>' fragment.
    """
    m = re.search(r"(<response\b.*?</response>)", response_text, flags=re.DOTALL | re.IGNORECASE)
    if not m:
        # maybe they already passed just the xml
        if response_text.strip().startswith("<response"):
            return response_text.strip()
        raise ValueError("Could not find <response> XML in text.")
    return m.group(1).strip()

def _t(text: Optional[str]) -> Optional[str]:
    """Trim; None if empty."""
    if text is None:
        return None
    s = text.strip()
    return s if s else None

def _bool(s: Optional[str]) -> Optional[bool]:
    if s is None:
        return None
    s = s.strip().lower()
    if s in ("true", "1", "y", "yes"):
        return True
    if s in ("false", "0", "n", "no"):
        return False
    return None

def _int(s: Optional[str]) -> Optional[int]:
    if s is None:
        return None
    try:
        return int(s.strip())
    except Exception:
        return None

def _dt(s: Optional[str]) -> Optional[str]:
    """
    Normalize strings like '2025-08-22T16:00:00.000' → ISO8601 '2025-08-22T16:00:00'.
    Return None if invalid.
    """
    if not s:
        return None
    s = s.strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            return dt.datetime.strptime(s, fmt).isoformat()
        except Exception:
            pass
    return None

def _date_only(iso_ts: Optional[str]) -> Optional[str]:
    if not iso_ts:
        return None
    try:
        return iso_ts.split("T")[0]
    except Exception:
        return None

def _text(node: Optional[ET.Element]) -> Optional[str]:
    return _t(node.text if node is not None else None)

def _unescape_newlines(s: Optional[str]) -> Optional[str]:
    """
    Evolution often encodes line breaks as &#xD; and entities like &amp;.
    Convert those to nice plain text with real newlines.
    """
    if s is None:
        return None
    s = html.unescape(s)
    s = s.replace("&#xD;", "\n").replace("\r", "\n")
    # collapse 3+ newlines to 2
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip() if s.strip() else None

# ---------------------------
# Core parsing
# ---------------------------

def parse_get_case_detail(response_text: str) -> Dict[str, Any]:
    """
    Main entry: raw API text → dict.
    """
    xml = _extract_xml(response_text)
    root = ET.fromstring(xml)

    # Basic fields
    case_id = _int(_text(root.find("case_id")))
    case_number = _text(root.find("case_number"))

    # Doctor
    doctor = {
        "id": _int(_text(root.find("doctor_id"))),
        "first_name": _text(root.find("doctor_fname")),
        "last_name": _text(root.find("doctor_lname")),
        "practice": _text(root.find("doctor_practice")),
        "ship_to": {
            "id": _int(_text(root.find("doctor_ship_id"))),
            "address1": _text(root.find("doctor_ship_addr1")),
            "address2": _text(root.find("doctor_ship_addr2")),
            "address3": _text(root.find("doctor_ship_addr3")),
            "city": _text(root.find("doctor_ship_city")),
            "state": _text(root.find("doctor_ship_state")),
            "zip": _text(root.find("doctor_ship_zip")),
            "country": _text(root.find("doctor_ship_country")),
            "phone": _text(root.find("doctor_ship_phone")),
        },
        "custom1": _text(root.find("doctor_custom1")),
        "custom2": _bool(_text(root.find("doctor_custom2"))),
    }

    # Case meta
    status_code = _text(root.find("case_status"))
    status_desc = _text(root.find("case_status_description"))
    type_code = _text(root.find("case_type"))
    type_desc = _text(root.find("case_type_description"))
    remake_reason_id = _text(root.find("case_remake_reason_id"))
    remake_reason = _text(root.find("case_remake_reason_description"))
    remake_source = _text(root.find("case_remake_casenumber"))
    remake_note = _text(root.find("case_remake_note"))

    preferences_raw = _text(root.find("case_preferences"))
    preferences = _unescape_newlines(preferences_raw)

    # Flags & simple fields
    rush = _bool(_text(root.find("case_rush")))
    has_imgs = _bool(_text(root.find("case_hasimgs")))
    has_attachments = _bool(_text(root.find("case_hasattachments")))
    has_notes = _bool(_text(root.find("case_hasnotes")))
    carrier = _text(root.find("case_carrier"))

    # Dates
    appointment = _dt(_text(root.find("patient_appointmentdate")))
    ship_date = _dt(_text(root.find("case_shippingdate")))
    ship_time = _t(_text(root.find("case_shippingtime")))  # keep raw time
    out_of_lab = _dt(_text(root.find("case_outoflab")))
    delivery_date = _dt(_text(root.find("case_deliverydate")))
    original_due = _dt(_text(root.find("case_originalduedate")))
    order_date = _dt(_text(root.find("case_orderdate")))

    # Patient
    patient = {
        "first_name": _text(root.find("case_pfname")),
        "middle_initial": _text(root.find("case_pmi")),
        "last_name": _text(root.find("case_plname")),
        "pan": _text(root.find("case_pannumber")),
    }

    # Location (lab/site id if present)
    location_id = _int(_text(root.find("case_location_id")))
    # Services
    services: List[Dict[str, Any]] = []
    services_node = root.find("case_services")
    if services_node is not None:
        for svc in services_node.findall("service"):
            tooth_items: List[Dict[str, Any]] = []
            toothlist = svc.find("service_toothlist")
            if toothlist is not None:
                for tnode in toothlist.findall("tooth"):
                    tooth_items.append({
                        "tooth_num": _text(tnode.find("tooth_num")),
                        "tooth_type": _text(tnode.find("tooth_type")),
                        "bridge": _bool(_text(tnode.find("bridge"))),
                        "shades": _text(tnode.find("shades")),
                    })
            services.append({
                "description": _text(svc.find("service_description")),
                "metal": _text(svc.find("service_metal")),
                "units": _int(_text(svc.find("service_units"))),
                "doctor_note": _unescape_newlines(_text(svc.find("service_drnote"))),
                "toothlist": tooth_items,
            })

    # Steps
    steps: List[Dict[str, Any]] = []
    steps_node = root.find("case_steps")
    if steps_node is not None:
        for st in steps_node.findall("step"):
            s_start = _dt(_text(st.find("step_startdate")))
            s_finish = _dt(_text(st.find("step_finishdate")))
            steps.append({
                "schedule_step_id": _int(_text(st.find("schedulestep_id"))),
                "base_step_id": _int(_text(st.find("basestep_id"))),
                "description": _text(st.find("step_description")),
                "skill_level_required": _int(_text(st.find("step_skilllevel"))),
                "employee": {
                    "id": _int(_text(st.find("employee_id"))),
                    "name": _text(st.find("employee_name")),
                    "skill_level": _int(_text(st.find("employee_skilllevel"))),
                    "tech_id": _text(st.find("employee_techid")),
                },
                "start": s_start,
                "finish": s_finish,
                "status_code": _text(st.find("step_status")),
                "status_description": _text(st.find("step_status_description")),
                "sequence_no": _int(_text(st.find("step_seqno"))),
                "start_date": _date_only(s_start),
                "finish_date": _date_only(s_finish),
            })

    # Tracking (may be blank)
    tracking_number = _text(root.find("case_trackingnumber"))
    tracking_url = _text(root.find("case_trackingurl"))

    # Build final structured dict
    payload: Dict[str, Any] = {
        "case": {
            "id": case_id,
            "number": case_number,
            "status_code": status_code,
            "status_description": status_desc,
            "type_code": type_code,
            "type_description": type_desc,
            "remake": {
                "reason_id": remake_reason_id,
                "reason_description": remake_reason,
                "source_case_number": _t(remake_source),
                "note": remake_note,
            },
            "preferences_text": preferences,             # clean newlines/entities
            "preferences_raw": preferences_raw,          # original raw string (optional for audits)
            "rush": rush,
            "flags": {
                "has_images": has_imgs,
                "has_attachments": has_attachments,
                "has_notes": has_notes,
            },
            "order_date": order_date,
            "original_due_date": original_due,
            "delivery_date": delivery_date,
            "out_of_lab_datetime": out_of_lab,
        },
        "doctor": doctor,
        "patient": patient,
        "logistics": {
            "carrier": carrier,
            "shipping_date": ship_date,
            "shipping_time": ship_time,                  # unchanged
            "appointment_datetime": appointment,
            "tracking_number": tracking_number,
            "tracking_url": tracking_url,
            "location_id": location_id,
            # Convenient date-only mirrors
            "shipping_day": _date_only(ship_date),
            "delivery_day": _date_only(delivery_date),
            "original_due_day": _date_only(original_due),
            "out_of_lab_day": _date_only(out_of_lab),
            "appointment_day": _date_only(appointment),
        },
        "services": services,
        "steps": steps,
        # Raw auth echoes exist in the XML; we deliberately omit username/password from output
    }

    return payload


# ---------------------------
# Quick smoke test (optional)
# ---------------------------
if __name__ == "__main__":
    sample = r'''Status: 200 Response: <response xmlns:i="http://www.w3.org/2001/XMLSchema-instance"><username>brett@absolutedentalservices.com</username><password>&lt;password&gt;</password><case_id>2469681</case_id><case_number>2025-46855</case_number><doctor_id>116530</doctor_id><doctor_fname>Abby</doctor_fname><doctor_lname>Dew</doctor_lname><doctor_practice>Dental Harbor</doctor_practice><doctor_ship_id>117287</doctor_ship_id><doctor_ship_addr1>50 Meeting Street</doctor_ship_addr1><doctor_ship_addr2>Suite B</doctor_ship_addr2><doctor_ship_addr3/><doctor_ship_city>Savannah</doctor_ship_city><doctor_ship_state>GA</doctor_ship_state><doctor_ship_zip>31411</doctor_ship_zip><doctor_ship_country>US</doctor_ship_country><doctor_ship_phone>(912) 480-0804</doctor_ship_phone><doctor_custom1/><doctor_custom2>false</doctor_custom2><case_status>S</case_status><case_status_description>In Process</case_status_description><case_type>N</case_type><case_type_description>New</case_type_description><case_remake_reason_id/><case_remake_reason_description/><case_remake_casenumber> </case_remake_casenumber><case_remake_note/><case_preferences>Email: vip@dentalharbor.com&#xD; &#xD; DO NOT SEND TO AI for Design! (JI 4-9-25)&#xD; &#xD; DESIGNERS - MARGINS SHOULD BE CLEAR WITH A SHOULDER. ANY QUESTIONS BRING TO TOMMY TO EVAL WITH DR. BEFORE DESIGNING.&#xD; &#xD; CROWNS - DESIGN WITH EXTRA DIE SPACER&#xD; Keep out of occlusion by 0.10mm (JI 5-15-25)&#xD; NO tight contacts&#xD; Per doctor default to modeless Envision &amp; Emax Zirconia Crown and Veneers&#xD; 4/17 Per Ms. Gina Dr. wants us to do check MODELS from now.&#xD; &#xD; 2/22- Per Jenny doctor agreed to do models for Emax veneer cases. &#xD; &#xD; 10/11/24 Per Dr. Abby Dew, if nothing is selected for DENTURES, please proceed with Standard Digital Denture as default.&#xD; &#xD; 8/11/25 - Please note for all cases that Office always wants Economy Denture Teeth (Card)</case_preferences><case_drpref/><case_rush>false</case_rush><case_tm_upperant/><case_tm_lowerant/><case_tm_posterior/><case_softtissueshade/><case_shade/><case_hasimgs>true</case_hasimgs><case_hasattachments>false</case_hasattachments><case_hasnotes>true</case_hasnotes><case_carrier>Next Day</case_carrier><patient_appointmentdate>2025-08-28T16:00:00.000</patient_appointmentdate><case_shippingdate>2025-08-22T00:00:00.000</case_shippingdate><case_shippingtime>16:00:00.000</case_shippingtime><case_outoflab>2025-08-22T16:00:00.000</case_outoflab><case_deliverydate>2025-08-28T00:00:00.000</case_deliverydate><case_originalduedate>2025-08-28T00:00:00.000</case_originalduedate><case_orderdate>2025-08-13T12:54:46.000</case_orderdate><case_pfname>Robert</case_pfname><case_pmi/><case_plname>Hulsey</case_plname><case_pannumber>2187</case_pannumber><case_location_id>1</case_location_id><case_services><service><service_description>Modeless Envision Posterior Crown</service_description><service_metal/><service_units>1</service_units><service_drnote/><service_toothlist><tooth><tooth_num>19</tooth_num><tooth_type/><bridge>false</bridge><shades>Vita Classic-A3.5</shades></tooth></service_toothlist></service><service><service_description>Digital Solid/Check Model</service_description><service_metal/><service_units>1</service_units><service_drnote/><service_toothlist/></service></case_services><case_steps><step><schedulestep_id>10343208</schedulestep_id><basestep_id>128</basestep_id><step_description>Zirconia Stain &amp; Glaze4</step_description><step_skilllevel>1</step_skilllevel><employee_id>-2</employee_id><employee_name>Zirconia Stain &amp; Glaze4</employee_name><employee_skilllevel>0</employee_skilllevel><employee_techid/><step_startdate>2025-08-21T00:00:00.000</step_startdate><step_finishdate>2025-08-21T00:00:00.000</step_finishdate><step_status>R</step_status><step_status_description>Ready</step_status_description><step_seqno>40</step_seqno></step><step><schedulestep_id>10343209</schedulestep_id><basestep_id>56</basestep_id><step_description>Final QC</step_description><step_skilllevel>2</step_skilllevel><employee_id>-2</employee_id><employee_name>Final QC</employee_name><employee_skilllevel>0</employee_skilllevel><employee_techid/><step_startdate>2025-08-22T00:00:00.000</step_startdate><step_finishdate>2025-08-22T00:00:00.000</step_finishdate><step_status>S</step_status><step_status_description>Scheduled</step_status_description><step_seqno>50</step_seqno></step><step><schedulestep_id>10343210</schedulestep_id><basestep_id>22</basestep_id><step_description>Shipping</step_description><step_skilllevel>2</step_skilllevel><employee_id>5</employee_id><employee_name>Shipping Department</employee_name><employee_skilllevel>6</employee_skilllevel><employee_techid>1</employee_techid><step_startdate>2025-08-22T00:00:00.000</step_startdate><step_finishdate>2025-08-22T00:00:00.000</step_finishdate><step_status>S</step_status><step_status_description>Scheduled</step_status_description><step_seqno>60</step_seqno></step></case_steps><case_materials/><post_casereceived_status/><case_trackingnumber/><case_trackingurl/></response>'''
    data = parse_get_case_detail(sample)
    import json
    print(json.dumps(data, indent=2))
