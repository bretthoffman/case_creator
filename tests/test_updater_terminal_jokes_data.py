import unittest

from pyside6_ui import UPDATER_DENTAL_JOKES_QA, _build_updater_powershell_script


class UpdaterTerminalJokesDataTests(unittest.TestCase):
    def test_exactly_forty_unique_joke_questions(self):
        self.assertEqual(len(UPDATER_DENTAL_JOKES_QA), 40)
        questions = [q for q, _a in UPDATER_DENTAL_JOKES_QA]
        self.assertEqual(len(questions), len(set(questions)))
        for q, a in UPDATER_DENTAL_JOKES_QA:
            self.assertTrue(q.strip())
            self.assertTrue(a.strip())

    def test_powershell_bundle_has_mb_progress_and_joke_stream(self):
        script = _build_updater_powershell_script()
        self.assertIn("Save-UpdateZipWithMbProgress", script)
        self.assertIn("Downloading update...", script)
        self.assertIn("While you wait, how about some jokes?", script)
        self.assertIn("Start-JokeRunspace", script)
        self.assertIn("Write-TypewriterToConsole", script)
        self.assertNotIn(
            "Invoke-WebRequest -Uri ([string]$job.zip_asset_url)",
            script,
        )


if __name__ == "__main__":
    unittest.main()
