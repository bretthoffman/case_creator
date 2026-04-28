from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from pyside6_ui import ensure_live_rules_folder_path_exists, get_live_rules_folder_path


class TestOpenRulesFolderPath(unittest.TestCase):
    def test_live_rules_folder_path_uses_localappdata_casecreator_v1(self) -> None:
        with patch.dict(os.environ, {"LOCALAPPDATA": r"C:\Users\Test\AppData\Local"}, clear=False):
            p = get_live_rules_folder_path()
        self.assertEqual(
            p,
            os.path.join(r"C:\Users\Test\AppData\Local", "CaseCreator", "business_rules", "v1"),
        )

    def test_ensure_live_rules_folder_creates_missing_path_only(self) -> None:
        with patch.dict(os.environ, {"LOCALAPPDATA": str(_REPO_ROOT / "tests" / "tmp_appdata_for_rules")}, clear=False):
            root = Path(os.environ["LOCALAPPDATA"]) / "CaseCreator"
            if root.exists():
                # Keep test isolated if a prior local run left artifacts.
                for child in sorted(root.rglob("*"), reverse=True):
                    if child.is_file():
                        child.unlink()
                    elif child.is_dir():
                        child.rmdir()
                root.rmdir()

            folder = Path(ensure_live_rules_folder_path_exists())
            self.assertTrue(folder.is_dir())
            self.assertEqual(folder, root / "business_rules" / "v1")
            self.assertEqual(list(folder.iterdir()), [], "button path creation must not create files")

            # cleanup
            folder.rmdir()
            (root / "business_rules").rmdir()
            root.rmdir()


if __name__ == "__main__":
    unittest.main()
