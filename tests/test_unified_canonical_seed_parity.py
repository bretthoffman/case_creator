"""
Ensure canonical unified config and packaged seed stay in sync.

Run: python -m unittest tests.test_unified_canonical_seed_parity -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

CANONICAL = _REPO_ROOT / "business_rules" / "v1" / "case_creator_rules.yaml"
SEED = _REPO_ROOT / "business_rules_seed" / "v1" / "case_creator_rules.yaml"


class TestUnifiedCanonicalSeedParity(unittest.TestCase):
    def test_canonical_and_seed_bytes_match(self) -> None:
        self.assertTrue(CANONICAL.is_file(), f"missing {CANONICAL}")
        self.assertTrue(SEED.is_file(), f"missing {SEED}")
        self.assertEqual(
            CANONICAL.read_bytes(),
            SEED.read_bytes(),
            "business_rules_seed must match canonical; run: python3 scripts/sync_unified_config_seed.py",
        )


if __name__ == "__main__":
    unittest.main()
