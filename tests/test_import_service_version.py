import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from import_service import get_app_info


class GetAppInfoVersionTests(unittest.TestCase):
    def test_env_var_overrides_files(self):
        with mock.patch.dict(os.environ, {"CASE_CREATOR_APP_VERSION": "9.9.9-test"}, clear=False):
            info = get_app_info()
        self.assertEqual(info["app_version"], "9.9.9-test")

    def test_reads_app_version_next_to_module(self):
        root = Path(__file__).resolve().parent.parent
        expected = (root / "app_version.txt").read_text(encoding="utf-8").strip()
        with mock.patch.dict(os.environ, {"CASE_CREATOR_APP_VERSION": ""}, clear=False):
            with mock.patch("import_service.sys._MEIPASS", None, create=True):
                info = get_app_info()
        self.assertEqual(info["app_version"], expected)
        self.assertNotEqual(info["app_version"], "")

    def test_meipass_candidate_used_when_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            av = Path(tmp) / "app_version.txt"
            av.write_text("1.2.3-from-meipass\n", encoding="utf-8")
            with mock.patch.dict(os.environ, {"CASE_CREATOR_APP_VERSION": ""}, clear=False):
                with mock.patch("import_service.sys._MEIPASS", str(tmp), create=True):
                    info = get_app_info()
            self.assertEqual(info["app_version"], "1.2.3-from-meipass")


if __name__ == "__main__":
    unittest.main()
