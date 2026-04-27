# evo_internal_client.py
import os, requests, urllib3
from typing import Dict, Any
from evolution_case_detail import parse_get_case_detail  # your working cleaner

EV_INT_BASE   = os.getenv("EV_INT_BASE", "https://192.168.1.6:9006")  # internal IP:PORT
EVO_USER      = os.getenv("EVO_USER", "steve@absolutedentalservices.com")
EVO_PASS      = os.getenv("EVO_PASS", "$85v5Rys78m923#8")
EVO_TIMEOUT   = float(os.getenv("EVO_TIMEOUT", "15"))
EVO_VERIFY_SSL = os.getenv("EVO_VERIFY_SSL", "false").lower() == "true"

if not EVO_VERIFY_SSL:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def _xml_request(case_number: str) -> bytes:
    return f"""<request>
  <username>{EVO_USER}</username>
  <password>{EVO_PASS}</password>
  <case_number>{case_number}</case_number>
</request>""".encode("utf-8")

def get_case_detail_clean(case_number: str) -> Dict[str, Any]:
    """
    Calls internal Evolution endpoint and returns your already-cleaned dict.
    """
    url = f"{EV_INT_BASE}/?event=wsb_get_casedetail"
    xml_payload = _xml_request(case_number)
    r = requests.post(
        url, data=xml_payload,
        headers={"Content-Type": "application/xml"},
        timeout=EVO_TIMEOUT,
        verify=EVO_VERIFY_SSL,
    )
    r.raise_for_status()
    # cleaner accepts either "Status: 200 Response: <response...>" or raw <response>…</response>
    # Build the wrapper string so the cleaner works either way:
    wrapped = f"Status: {r.status_code} Response: {r.text}"
    return parse_get_case_detail(wrapped)
