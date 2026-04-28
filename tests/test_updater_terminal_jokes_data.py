import unittest

from pyside6_ui import (
    UPDATER_DENTAL_JOKES_QA,
    _build_updater_powershell_script,
    updater_job_jokes_for_payload,
)


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
        self.assertIn("function Emit-MbProgress", script)
        self.assertIn("$got = [long]0", script)
        self.assertIn("Emit-MbProgress -BytesSoFar $got", script)
        self.assertIn("While you wait, how about some jokes?", script)
        self.assertIn("Start-JokeRunspace", script)
        self.assertIn("Write-TypewriterToConsole", script)
        self.assertNotIn(
            "Invoke-WebRequest -Uri ([string]$job.zip_asset_url)",
            script,
        )
        self.assertIn("IMMEDIATE: Case Creator updater script entry", script)
        self.assertNotIn("[pscustomobject]@", script)
        self.assertNotIn("$script:DentalJokes", script)
        self.assertIn("$job.jokes", script)

    def test_job_payload_jokes_round_trip_shape(self):
        jokes = updater_job_jokes_for_payload()
        self.assertEqual(len(jokes), 40)
        self.assertEqual(jokes[0]["q"], UPDATER_DENTAL_JOKES_QA[0][0])
        self.assertEqual(jokes[0]["a"], UPDATER_DENTAL_JOKES_QA[0][1])
        self.assertEqual(jokes[-1]["q"], UPDATER_DENTAL_JOKES_QA[-1][0])


if __name__ == "__main__":
    unittest.main()
