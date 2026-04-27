# local_evo_tester.py  — super-simple Evolution tester for LOCAL/INTERNAL relay
import os, sys, re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import requests
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

EVO_TEST_URL   = "http://192.168.3.211:5000/evo"   # your local/lan relay URL
EVO_USER       = "brett@absolutedentalservices.com"
EVO_PASS       = "U9A*V5B9p)828Umj"
EVO_RELAY_TOKEN= "lombardo"   # if your relay expects it; otherwise omit
EVO_VERIFY_TLS = "false"      # http or self-signed https

# ---- minimal config ----
BASE_URL   = EVO_TEST_URL
VERIFY_TLS = str(EVO_VERIFY_TLS).lower() in ("1","true","yes","on")  # ✅ fixed
RELAY_TOKEN= EVO_RELAY_TOKEN

# default event/body if you just run `python local_evo_tester.py`
DEFAULT_EVENT = "wsb_get_casedetail"
DEFAULT_BODY  = "<case_number>2025-53019</case_number>"

def with_event(url: str, event: str) -> str:
    u = urlparse(url)
    qs = parse_qs(u.query)
    qs["event"] = [event]
    query = urlencode({k: v[0] for k, v in qs.items()})
    return urlunparse((u.scheme, u.netloc, u.path, u.params, query, u.fragment))

def build_xml(inner: str, user: str, pw: str) -> str:
    return f"<request><username>{user}</username><password>{pw}</password>{inner}</request>"

def main():
    if not EVO_USER or not EVO_PASS:
        print("Set EVO_USER and EVO_PASS in this file (or swap to env vars).")
        sys.exit(1)

    # CLI usage:
    #   python local_evo_tester.py                            # uses DEFAULT_EVENT/BODY
    #   python local_evo_tester.py wsb_get_activecases ""     # no body
    #   python local_evo_tester.py wsb_get_casefiles "<case_number>2025-53019</case_number>"
    event = sys.argv[1] if len(sys.argv) >= 2 else DEFAULT_EVENT
    body  = sys.argv[2] if len(sys.argv) >= 3 else DEFAULT_BODY

    url = with_event(BASE_URL, event)
    xml = build_xml(body, EVO_USER, EVO_PASS)
    headers = {"Content-Type": "application/xml"}
    if RELAY_TOKEN:
        headers["X-Relay-Token"] = RELAY_TOKEN

    try:
        r = requests.post(url, data=xml.encode("utf-8"), headers=headers,
                          timeout=20, verify=VERIFY_TLS)
    except requests.ConnectionError as e:
        print("Connection error (refused/host down):", e)
        print(f"- Check host/port reachable: {BASE_URL}")
        print("- Is the relay service running and listening on this interface?")
        print("- If it's only on 127.0.0.1, use that IP; if it binds to 0.0.0.0, use the LAN IP.")
        sys.exit(2)
    except requests.RequestException as e:
        print("Request failed:", e); sys.exit(2)

    print("Status:", r.status_code)
    m = re.search(r"(<response\b.*?</response>)", r.text, flags=re.DOTALL|re.IGNORECASE)
    print(m.group(1) if m else r.text)

if __name__ == "__main__":   # ✅ added
    main()

