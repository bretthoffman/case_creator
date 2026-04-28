import os
import tempfile
import unittest
from unittest import mock

from pyside6_ui import append_updater_client_log, get_updater_log_path, get_updater_state_dir


class UpdaterClientLoggingTests(unittest.TestCase):
    def test_updater_paths_under_localappdata_casecreator_update(self):
        local = r"C:\Users\X\AppData\Local"
        with mock.patch.dict(os.environ, {"LOCALAPPDATA": local}, clear=False):
            self.assertEqual(
                get_updater_state_dir(),
                os.path.join(local, "CaseCreator", "update"),
            )
            self.assertEqual(
                get_updater_log_path(),
                os.path.join(local, "CaseCreator", "update", "updater.log"),
            )

    def test_append_updater_client_log_writes_stable_filename(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake_local = os.path.join(tmp, "Local")
            os.makedirs(fake_local, exist_ok=True)
            with mock.patch.dict(os.environ, {"LOCALAPPDATA": fake_local}, clear=False):
                log_path = get_updater_log_path()
                append_updater_client_log("hello from test")
            self.assertTrue(os.path.isfile(log_path))
            with open(log_path, encoding="utf-8") as handle:
                text = handle.read()
            self.assertIn("[client] hello from test", text)


if __name__ == "__main__":
    unittest.main()
