#!/usr/bin/env python3
"""
EVO Terminal Probe — raw XML tester (LAN only)
Usage examples (PowerShell/CMD):
  # By case number
  python evo_terminal_probe.py get_casedetail case_number=2025-46855
  # Files attached to a case
  python evo_terminal_probe.py get_casefiles case_number=2025-46855
  # Case steps
  python evo_terminal_probe.py get_casesteps case_number=2025-46855
  # Active cases in a window (field names depend on your EVO WS)
  python evo_terminal_probe.py get_activecases start_date=2025-09-01 end_date=2025-09-12 status=S
  # If your server expects different tag names, just pass them as key=value.
"""
import argparse, sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import requests, urllib3, textwrap
from typing import Dict
# Pull your internal settings + creds from the same place as your importer
from config import EV_INT_BASE, EVO_USER, EVO_PASS, EVO_TIMEOUT, EVO_VERIFY_SSL  # ← uses your real values
if not EVO_VERIFY_SSL:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# Friendly aliases → actual EVO event names
PRESETS = {
    "get_casedetail": "wsb_get_casedetail",
    "get_casefiles": "wsb_get_casefiles",
    "get_casesteps": "wsb_get_casesteps",
    "get_activecases": "wsb_get_activecases",
    # Add more here as you discover them:
    # "get_casedetail_byname": "wsb_get_casedetail_byname",
}
def build_xml(extra_fields: Dict[str, str]) -> bytes:
    # Build a generic <request> with whatever extra fields you pass in
    lines = [
        "<request>",
        f"  <username>{EVO_USER}</username>",
        f"  <password>{EVO_PASS}</password>",
    ]
    for k, v in extra_fields.items():
        lines.append(f"  <{k}>{v}</{k}>")
    lines.append("</request>")
    return ("\n".join(lines)).encode("utf-8")
def call_event(event: str, fields: Dict[str, str]) -> requests.Response:
    url = f"{EV_INT_BASE}/?event={event}"
    xml_payload = build_xml(fields)
    headers = {"Content-Type": "application/xml"}
    resp = requests.post(
        url, data=xml_payload, headers=headers,
        timeout=EVO_TIMEOUT, verify=EVO_VERIFY_SSL
    )
    return resp
def parse_kv(pairs):
    out = {}
    for item in pairs or []:
        if "=" not in item:
            print(f"[warn] ignoring '{item}' (expected key=value)", file=sys.stderr)
            continue
        k, v = item.split("=", 1)
        out[k.strip()] = v.strip()
    return out
def main():
    ap = argparse.ArgumentParser(description="Post raw XML to EVO and print the raw response.")
    ap.add_argument("event", help="Event preset (e.g., get_casedetail) OR raw event name (e.g., wsb_get_casedetail)")
    ap.add_argument("pairs", nargs="*", help="Extra XML fields as key=value (e.g., case_number=2025-46855)")
    ap.add_argument("--raw", action="store_true", help="Print only response body")
    ap.add_argument("--save", metavar="FILE", help="Optionally save body to a file")
    args = ap.parse_args()
    event_name = PRESETS.get(args.event, args.event)  # allow preset or full event
    fields = parse_kv(args.pairs)
    # Small sanity echo (mask password)
    xml_preview = textwrap.shorten(
        f"<request><username>{EVO_USER}</username><password>******</password>{''.join([f'<{k}>{v}</{k}>' for k,v in fields.items()])}</request>",
        width=200, placeholder="...")
    try:
        resp = call_event(event_name, fields)
    except requests.RequestException as e:
        print(f"[error] request failed: {e}", file=sys.stderr)
        sys.exit(2)
    if args.raw:
        print(resp.text)
    else:
        print(f"URL: {EV_INT_BASE}/?event={event_name}")
        print(f"XML: {xml_preview}")
        print(f"Status: {resp.status_code}")
        ctype = resp.headers.get("Content-Type", "")
        print(f"Content-Type: {ctype}")
        print("-" * 60)
        print(resp.text)
    if args.save:
        try:
            with open(args.save, "w", encoding="utf-8") as f:
                f.write(resp.text)
            print(f"[info] saved body to {args.save}")
        except Exception as e:
            print(f"[warn] couldn't save to {args.save}: {e}", file=sys.stderr)
if __name__ == "__main__":
    main()