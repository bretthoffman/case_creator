from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from pyside6_ui import get_live_rules_folder_path


class TestOpenRulesFolderPath(unittest.TestCase):
    def test_live_rules_folder_path_uses_localappdata_casecreator_v1(self) -> None:
        with patch.dict(os.environ, {"LOCALAPPDATA": r"C:\Users\Test\AppData\Local"}, clear=False):
            p = get_live_rules_folder_path()
        self.assertEqual(
            p,
            os.path.join(r"C:\Users\Test\AppData\Local", "CaseCreator", "business_rules", "v1"),
        )


if __name__ == "__main__":
    unittest.main()
