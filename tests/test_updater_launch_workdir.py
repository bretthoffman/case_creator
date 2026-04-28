import os
import tempfile
import unittest
from unittest import mock

from pyside6_ui import get_install_root_path, launch_external_updater
from update_check import STATUS_UPDATE_AVAILABLE, UpdateCheckResult


class UpdaterLaunchWorkdirTests(unittest.TestCase):
    def test_popen_uses_runner_dir_as_cwd_not_install_root(self):
        """Updater child process must not inherit CWD from the app install folder (locks swap)."""
        with tempfile.TemporaryDirectory() as tmp:
            captured = {}

            def fake_popen(*args, **kwargs):
                captured["argv"] = args[0]
                captured["kwargs"] = kwargs
                mock_proc = mock.MagicMock()
                mock_proc.pid = 99999
                mock_proc.poll.return_value = None
                return mock_proc

            result = UpdateCheckResult(
                status=STATUS_UPDATE_AVAILABLE,
                current_version="1.0.0",
                latest_tag="v1.0.1",
                zip_asset_url="https://example.com/CaseCreator-1-win64.zip",
                zip_asset_name="CaseCreator-1-win64.zip",
            )
            with mock.patch("pyside6_ui.os.name", "nt"):
                with mock.patch("pyside6_ui.tempfile.gettempdir", return_value=tmp):
                    with mock.patch("pyside6_ui.subprocess.Popen", side_effect=fake_popen):
                        with mock.patch("pyside6_ui.append_updater_client_log"):
                            launch_external_updater(result, "1.0.0")

            install_root = get_install_root_path()
            cwd = captured["kwargs"].get("cwd")
            argv = captured["argv"]
            self.assertIsNotNone(cwd)
            self.assertTrue(os.path.normcase(cwd).startswith(os.path.normcase(tmp)))
            self.assertNotEqual(
                os.path.normcase(os.path.abspath(cwd)),
                os.path.normcase(os.path.abspath(install_root)),
            )
            self.assertGreaterEqual(len(argv), 4)
            self.assertEqual(argv[1].lower(), "/c")
            self.assertTrue(
                str(argv[2]).lower().endswith("case_creator_updater.cmd"),
                msg=f"expected .cmd launcher in argv, got {argv!r}",
            )
            self.assertTrue(str(argv[3]).endswith(".json"))


if __name__ == "__main__":
    unittest.main()
