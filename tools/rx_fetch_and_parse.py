# rx_fetch_and_parse.py
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import os, requests, urllib.parse
from config import EV_INT_BASE, EVO_USER, EVO_PASS, EVO_TIMEOUT, EVO_VERIFY_SSL
import urllib3
if not EVO_VERIFY_SSL:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
def post_xml(event, fields):
    body = ["<request>", f"<username>{EVO_USER}</username>", f"<password>{EVO_PASS}</password>"]
    for k,v in fields.items(): body.append(f"<{k}>{v}</{k}>")
    body.append("</request>")
    url = f"{EV_INT_BASE}/?event={event}"
    return requests.post(url, data="\n".join(body).encode("utf-8"),
                         headers={"Content-Type":"application/xml"},
                         timeout=EVO_TIMEOUT, verify=EVO_VERIFY_SSL)
def extract_text_from_pdf(path):
    # Simple, built-in-only fallback: return bytes length if PyPDF2 isn't available
    try:
        import PyPDF2
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            return "\n".join([page.extract_text() or "" for page in reader.pages])[:4000]
    except Exception as e:
        return f"[note] Could not parse text via PyPDF2: {e}. File saved at: {path}"
def main():
    if len(sys.argv) != 2:
        print("Usage: python rx_fetch_and_parse.py <case_id>")
        sys.exit(1)
    case_id = sys.argv[1]
    r = post_xml("wsb_get_casefiles", {"case_id": case_id})
    r.raise_for_status()
    xml = r.text
    # crude pulls—good enough for a probe
    urls = []
    start = 0
    while True:
        a = xml.find("<image_url>", start)
        if a == -1: break
        b = xml.find("</image_url>", a)
        urls.append(xml[a+11:b])
        start = b+12
    if not urls:
        print("[info] No image_url entries found.")
        print(xml)
        return
    os.makedirs("rx_downloads", exist_ok=True)
    for i, url in enumerate(urls, 1):
        # ensure proper encoding of spaces, etc.
        url = urllib.parse.quote(url, safe=":/%?=&()-_.")
        print(f"[dl] GET {url}")
        # --- START new robust fetch block ---
        import re
        from urllib.parse import urlparse, urlunparse

        # 0) optionally force internal host (flip to True to try LAN first)
        FORCE_INTERNAL_HOST = True
        INTERNAL_HOST = "192.168.1.6"   # your EVO server host/IP on LAN
        INTERNAL_PORT = 8051            # same as the image server port
        if FORCE_INTERNAL_HOST:
            pu = urlparse(url)
            # keep scheme/path/query, swap netloc to internal
            netloc = f"{INTERNAL_HOST}:{INTERNAL_PORT}"
            url_try = urlunparse((pu.scheme, netloc, pu.path, pu.params, pu.query, pu.fragment))
        else:
            url_try = url

        s = requests.Session()
        s.verify = False  # image server is http in your example; leave False for https self-signed too

        def save_bytes(content, suffix):
            fname = f"rx_downloads/case_{case_id}_{i}{suffix}"
            with open(fname, "wb") as f:
                f.write(content)
            print(f"[ok] saved -> {fname} ({len(content)} bytes)")
            return fname

        # 1) no-auth attempt
        r = s.get(url_try, timeout=60)
        auth_hdr = r.headers.get("WWW-Authenticate", "")
        if r.status_code == 401:
            print(f"[info] 401 Unauthorized. WWW-Authenticate: {auth_hdr}")

        # 2) If 401, try Basic with EVO creds
        # 2) If 401, try Basic with image server creds
        if r.status_code == 401:
            from requests.auth import HTTPBasicAuth
            try:
                from config import IMG_USER, IMG_PASS
            except ImportError:
                IMG_USER = IMG_PASS = ""
            if IMG_USER and IMG_PASS:
                print(f"[info] Trying Basic auth with IMG_USER from config: {IMG_USER}")
                r = s.get(url_try, timeout=60, auth=HTTPBasicAuth(IMG_USER, IMG_PASS))
            else:
                print("[warn] No IMG_USER/IMG_PASS set in config.py")

        # 3) If still 401, try NTLM (Windows Integrated)
        if r.status_code == 401:
            try:
                from requests_ntlm import HttpNtlmAuth  # pip install requests-ntlm
                # Heuristic: if your EVO_USER is an email, you might need DOMAIN\username.
                # We'll try without a domain first; if you know the domain, set DOMAIN below.
                DOMAIN = ""  # e.g., "ADS" → then use f"{DOMAIN}\\{USERNAME}"
                if "\\" in EVO_USER:
                    ntlm_user = EVO_USER
                elif DOMAIN:
                    ntlm_user = f"{DOMAIN}\\{EVO_USER}"
                else:
                    ntlm_user = EVO_USER
                r = s.get(url_try, timeout=60, auth=HttpNtlmAuth(ntlm_user, EVO_PASS))
                if r.status_code == 401:
                    print(f"[info] NTLM failed. WWW-Authenticate: {r.headers.get('WWW-Authenticate','')}")
            except Exception as e:
                print(f"[info] NTLM not attempted (install requests-ntlm). Error: {e}")

        # Save whatever we got for inspection
        if r.ok and r.content:
            saved = save_bytes(r.content, ".pdf")
        else:
            # Save the body (likely HTML error)
            saved = save_bytes(r.content or b"", ".html")
            print(f"[warn] Non-OK response {r.status_code}. Body saved for inspection.")
        # --- END new robust fetch block ---

if __name__ == "__main__":
    main()