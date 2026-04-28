from __future__ import annotations

import json
import os
import sys
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from update_check import (
    DEFAULT_GITHUB_REPO,
    STATUS_FAILURE,
    STATUS_UP_TO_DATE,
    STATUS_UPDATE_AVAILABLE,
    check_github_latest_release,
    is_update_available,
    select_release_assets,
)


class _FakeResponse(BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class TestUpdateCheck(unittest.TestCase):
    def test_default_github_repo_target(self):
        self.assertEqual(DEFAULT_GITHUB_REPO, "bretthoffman/case_creator")

    def test_is_update_available_handles_v_prefix_and_prerelease(self):
        self.assertTrue(is_update_available("0.0.2-test", "v0.0.2"))
        self.assertFalse(is_update_available("0.0.2", "v0.0.2"))
        self.assertFalse(is_update_available("0.0.3", "v0.0.2"))

    def test_check_github_latest_release_update_available(self):
        payload = {
            "tag_name": "v1.2.3",
            "html_url": "https://github.com/example/repo/releases/tag/v1.2.3",
            "assets": [
                {
                    "name": "CaseCreator-v1.2.3-win64.zip",
                    "browser_download_url": "https://example.test/CaseCreator-v1.2.3-win64.zip",
                },
                {
                    "name": "CaseCreator-v1.2.3-win64.zip.sha256",
                    "browser_download_url": "https://example.test/CaseCreator-v1.2.3-win64.zip.sha256",
                },
            ],
        }
        with patch("update_check.urlopen", return_value=_FakeResponse(json.dumps(payload).encode("utf-8"))):
            result = check_github_latest_release(current_version="1.0.0")
        self.assertEqual(result.status, STATUS_UPDATE_AVAILABLE)
        self.assertEqual(result.latest_tag, "v1.2.3")
        self.assertEqual(result.zip_asset_name, "CaseCreator-v1.2.3-win64.zip")
        self.assertEqual(
            result.zip_asset_url,
            "https://example.test/CaseCreator-v1.2.3-win64.zip",
        )
        self.assertEqual(
            result.checksum_asset_url,
            "https://example.test/CaseCreator-v1.2.3-win64.zip.sha256",
        )

    def test_check_github_latest_release_up_to_date(self):
        payload = {"tag_name": "v1.0.0", "html_url": "https://example.test/release"}
        with patch("update_check.urlopen", return_value=_FakeResponse(json.dumps(payload).encode("utf-8"))):
            result = check_github_latest_release(current_version="1.0.0")
        self.assertEqual(result.status, STATUS_UP_TO_DATE)

    def test_check_github_latest_release_handles_failure(self):
        with patch("update_check.urlopen", side_effect=Exception("boom")):
            result = check_github_latest_release(current_version="1.0.0")
        self.assertEqual(result.status, STATUS_FAILURE)

    def test_env_override_repo_is_used(self):
        payload = {"tag_name": "v1.0.0", "html_url": "https://example.test/release"}

        def _fake_urlopen(req, timeout=0):
            self.assertIn("repos/custom-owner/custom-repo/releases/latest", req.full_url)
            return _FakeResponse(json.dumps(payload).encode("utf-8"))

        with patch.dict(os.environ, {"CASE_CREATOR_GITHUB_REPO": "custom-owner/custom-repo"}, clear=False):
            with patch("update_check.urlopen", side_effect=_fake_urlopen):
                result = check_github_latest_release(current_version="1.0.0")
        self.assertEqual(result.status, STATUS_UP_TO_DATE)

    def test_select_release_assets_ignores_source_archives(self):
        payload = {
            "assets": [
                {"name": "source code.zip", "browser_download_url": "https://example/source.zip"},
                {"name": "source code.tar.gz", "browser_download_url": "https://example/source.tgz"},
                {
                    "name": "CaseCreator-v2.0.0-win64.zip",
                    "browser_download_url": "https://example/CaseCreator-v2.0.0-win64.zip",
                },
            ]
        }
        name, zip_url, checksum_url = select_release_assets(payload)
        self.assertEqual(name, "CaseCreator-v2.0.0-win64.zip")
        self.assertEqual(zip_url, "https://example/CaseCreator-v2.0.0-win64.zip")
        self.assertIsNone(checksum_url)


if __name__ == "__main__":
    unittest.main()
