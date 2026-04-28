from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Optional
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen

DEFAULT_GITHUB_REPO = "bretthoffman/case_creator"
DEFAULT_GITHUB_RELEASES_LATEST_API = (
    "https://api.github.com/repos/{repo}/releases/latest"
)

STATUS_UP_TO_DATE = "up_to_date"
STATUS_UPDATE_AVAILABLE = "update_available"
STATUS_FAILURE = "failure"


@dataclass(frozen=True)
class UpdateCheckResult:
    status: str
    current_version: str
    latest_tag: Optional[str] = None
    latest_version: Optional[str] = None
    release_url: Optional[str] = None
    zip_asset_name: Optional[str] = None
    zip_asset_url: Optional[str] = None
    checksum_asset_url: Optional[str] = None
    error: Optional[str] = None


def normalize_tag_version(tag: str) -> str:
    return (tag or "").strip().lstrip("vV")


_VERSION_RE = re.compile(r"^\s*(\d+)\.(\d+)\.(\d+)(?:[-+].*)?\s*$")
_RELEASE_ZIP_NAME_RE = re.compile(r"^CaseCreator-.*-win64\.zip$", re.IGNORECASE)


def _parse_bounded_version(value: str) -> Optional[tuple[int, int, int, bool]]:
    """
    Bounded parser for tags like:
    - 1.2.3
    - v1.2.3
    - v0.0.2-test
    Returns (major, minor, patch, is_prerelease_like).
    """
    norm = normalize_tag_version(value)
    if not norm:
        return None
    m = _VERSION_RE.match(norm)
    if not m:
        return None
    major, minor, patch = int(m.group(1)), int(m.group(2)), int(m.group(3))
    is_prerelease_like = "-" in norm
    return major, minor, patch, is_prerelease_like


def is_update_available(current_version: str, latest_tag: str) -> bool:
    """
    Conservative comparison:
    - Parse bounded `vMAJOR.MINOR.PATCH[-suffix]` shape.
    - Compare major/minor/patch numerically.
    - For same numeric version: a stable release is newer than prerelease-like current.
    - If parsing fails for either side, treat only exact normalized mismatch as update.
    """
    cur_v = _parse_bounded_version(current_version)
    latest_v = _parse_bounded_version(latest_tag)
    if cur_v is not None and latest_v is not None:
        cur_triplet = cur_v[:3]
        latest_triplet = latest_v[:3]
        if latest_triplet != cur_triplet:
            return latest_triplet > cur_triplet
        # same numeric version: stable latest beats prerelease current
        cur_pre = cur_v[3]
        latest_pre = latest_v[3]
        return (not latest_pre) and cur_pre
    return normalize_tag_version(latest_tag) != normalize_tag_version(current_version)


def select_release_assets(release_payload: dict[str, Any]) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Returns (zip_asset_name, zip_asset_url, checksum_asset_url) for the packaged win64 release zip.
    Ignores source archives and unrelated assets.
    """
    assets = release_payload.get("assets")
    if not isinstance(assets, list):
        return None, None, None

    zip_name = None
    zip_url = None
    checksum_url = None
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        name = str(asset.get("name") or "").strip()
        url = str(asset.get("browser_download_url") or "").strip()
        if not name or not url:
            continue
        if zip_name is None and _RELEASE_ZIP_NAME_RE.match(name):
            zip_name = name
            zip_url = url
            continue

    if zip_name:
        checksum_name = f"{zip_name}.sha256"
        for asset in assets:
            if not isinstance(asset, dict):
                continue
            name = str(asset.get("name") or "").strip()
            url = str(asset.get("browser_download_url") or "").strip()
            if name == checksum_name and url:
                checksum_url = url
                break

    return zip_name, zip_url, checksum_url


def check_github_latest_release(
    *,
    current_version: str,
    github_repo: Optional[str] = None,
    timeout_seconds: float = 8.0,
) -> UpdateCheckResult:
    repo = (github_repo or os.getenv("CASE_CREATOR_GITHUB_REPO") or DEFAULT_GITHUB_REPO).strip()
    url = DEFAULT_GITHUB_RELEASES_LATEST_API.format(repo=repo)
    req = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "case-creator-update-check",
        },
    )
    try:
        with urlopen(req, timeout=timeout_seconds) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        payload = json.loads(raw)
    except HTTPError as exc:
        return UpdateCheckResult(
            status=STATUS_FAILURE,
            current_version=current_version,
            error=f"GitHub HTTP error: {exc.code}",
        )
    except URLError as exc:
        return UpdateCheckResult(
            status=STATUS_FAILURE,
            current_version=current_version,
            error=f"Network error: {exc.reason}",
        )
    except Exception as exc:
        return UpdateCheckResult(
            status=STATUS_FAILURE,
            current_version=current_version,
            error=f"Update check failed: {exc}",
        )

    latest_tag = str(payload.get("tag_name") or "").strip()
    if not latest_tag:
        return UpdateCheckResult(
            status=STATUS_FAILURE,
            current_version=current_version,
            error="Latest release did not include a tag.",
        )

    latest_version = normalize_tag_version(latest_tag)
    release_url = str(payload.get("html_url") or "").strip() or None
    zip_asset_name, zip_asset_url, checksum_asset_url = select_release_assets(payload)
    if is_update_available(current_version, latest_tag):
        return UpdateCheckResult(
            status=STATUS_UPDATE_AVAILABLE,
            current_version=current_version,
            latest_tag=latest_tag,
            latest_version=latest_version,
            release_url=release_url,
            zip_asset_name=zip_asset_name,
            zip_asset_url=zip_asset_url,
            checksum_asset_url=checksum_asset_url,
        )
    return UpdateCheckResult(
        status=STATUS_UP_TO_DATE,
        current_version=current_version,
        latest_tag=latest_tag,
        latest_version=latest_version,
        release_url=release_url,
        zip_asset_name=zip_asset_name,
        zip_asset_url=zip_asset_url,
        checksum_asset_url=checksum_asset_url,
    )
