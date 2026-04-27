#!/usr/bin/env python3
"""
Copy the canonical unified business-rules file into the packaged-seed path.

Canonical (human-edited in repo / source-dev live file):
  business_rules/v1/case_creator_rules.yaml

Packaged default seed (bundled artifact for PyInstaller first-run seeding):
  business_rules_seed/v1/case_creator_rules.yaml

Run from repo root after editing the canonical file:
  python3 scripts/sync_unified_config_seed.py

The Windows release build script also copies the canonical file into the seed path before PyInstaller.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CANONICAL = _REPO_ROOT / "business_rules" / "v1" / "case_creator_rules.yaml"
_SEED_DIR = _REPO_ROOT / "business_rules_seed" / "v1"
_SEED = _SEED_DIR / "case_creator_rules.yaml"


def main() -> int:
    if not _CANONICAL.is_file():
        print(f"ERROR: missing canonical file: {_CANONICAL}", file=sys.stderr)
        return 1
    _SEED_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(_CANONICAL, _SEED)
    print(f"OK: synced {_CANONICAL} -> {_SEED}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
