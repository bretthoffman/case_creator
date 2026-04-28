import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import yaml

from infrastructure.config.business_rule_models import (
    BusinessRuleConfigPreview,
    BusinessRuleFileReport,
    UnifiedRuntimePaths,
    ValidationResult,
)
from infrastructure.config import business_rule_schemas as schemas

_LOG = logging.getLogger(__name__)

# Deterministic order: prefer .yaml, then .yml (only one is used; both existing yields a warning).
UNIFIED_RULES_FILENAMES = ("case_creator_rules.yaml", "case_creator_rules.yml")
BUNDLED_SEED_RELATIVE_PATH = Path("business_rules_seed") / "v1" / "case_creator_rules.yaml"


def _is_frozen_windows() -> bool:
    return os.name == "nt" and bool(getattr(sys, "frozen", False))


def discover_business_rules_base_dir(override_base_dir: Optional[str] = None) -> Tuple[str, str]:
    """
    Returns (base_dir, mode).
    mode is 'frozen_windows' or 'source'.
    """
    if override_base_dir:
        return str(Path(override_base_dir)), "override"

    env_override = (os.getenv("CASE_CREATOR_BUSINESS_RULES_DIR") or "").strip()
    if env_override:
        return str(Path(env_override)), "env_override"

    if _is_frozen_windows():
        local_appdata = os.getenv("LOCALAPPDATA") or os.path.expanduser("~")
        return str(Path(local_appdata) / "CaseCreator" / "business_rules" / "v1"), "frozen_windows"

    project_root = Path(__file__).resolve().parents[2]
    return str(project_root / "business_rules" / "v1"), "source"


def _resolve_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_bundled_seed_path(*, bundled_root_override: Optional[str] = None) -> Path:
    if bundled_root_override:
        return Path(bundled_root_override) / BUNDLED_SEED_RELATIVE_PATH
    candidates: List[Path] = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / BUNDLED_SEED_RELATIVE_PATH)

    # Some frozen one-folder layouts place add-data files next to the executable.
    exe_dir = Path(getattr(sys, "executable", "")).resolve().parent if getattr(sys, "executable", "") else None
    if exe_dir is not None:
        candidates.append(exe_dir / BUNDLED_SEED_RELATIVE_PATH)

    candidates.append(_resolve_project_root() / BUNDLED_SEED_RELATIVE_PATH)

    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return candidates[0]


def resolve_unified_runtime_paths(
    override_base_dir: Optional[str] = None,
    *,
    force_frozen_windows: Optional[bool] = None,
    local_appdata_override: Optional[str] = None,
    bundled_root_override: Optional[str] = None,
) -> UnifiedRuntimePaths:
    """
    Resolve mode + live unified path (+ bundled seed path for packaged mode).

    This helper is intentionally side-effect free; file/directory creation happens in the
    seed helper.
    """
    base_dir, mode = discover_business_rules_base_dir(override_base_dir=override_base_dir)
    base_path = Path(base_dir)
    live = base_path / UNIFIED_RULES_FILENAMES[0]

    frozen = _is_frozen_windows() if force_frozen_windows is None else force_frozen_windows
    if mode not in ("override", "env_override") and frozen:
        appdata_root = Path(local_appdata_override or os.getenv("LOCALAPPDATA") or os.path.expanduser("~"))
        packaged_base = appdata_root / "CaseCreator" / "business_rules" / "v1"
        return UnifiedRuntimePaths(
            mode="frozen_windows",
            base_dir=str(packaged_base),
            live_unified_path=str(packaged_base / UNIFIED_RULES_FILENAMES[0]),
            bundled_seed_path=str(_resolve_bundled_seed_path(bundled_root_override=bundled_root_override)),
        )

    return UnifiedRuntimePaths(
        mode=mode,
        base_dir=str(base_path),
        live_unified_path=str(live),
        bundled_seed_path=None,
    )


def _read_structured_file(path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    try:
        with path.open("r", encoding="utf-8") as f:
            suffix = path.suffix.lower()
            if suffix in (".yaml", ".yml"):
                data = yaml.safe_load(f)
                if data is None:
                    data = {}
            elif suffix == ".json":
                data = json.load(f)
            else:
                return None, f"Unsupported file extension: {suffix}"
        if not isinstance(data, dict):
            return None, "Top-level config must be an object."
        return data, None
    except FileNotFoundError:
        return None, None
    except yaml.YAMLError as exc:
        return None, f"Malformed YAML: {exc}"
    except json.JSONDecodeError as exc:
        return None, f"Malformed JSON: {exc}"
    except Exception as exc:
        return None, f"Failed to read file: {exc}"


def _pick_unified_file(base_path: Path) -> Tuple[Optional[Path], List[str]]:
    warnings: List[str] = []
    existing = [name for name in UNIFIED_RULES_FILENAMES if (base_path / name).exists()]
    if not existing:
        return None, warnings
    chosen = existing[0]
    if len(existing) > 1:
        warnings.append(
            f"Multiple unified rules files found; using {chosen} and ignoring {existing[1:]}."
        )
    return base_path / chosen, warnings


def _seed_frozen_external_unified_if_missing(paths: UnifiedRuntimePaths) -> Tuple[List[str], List[str]]:
    """
    Packaged-mode helper: ensure the external unified file exists.
    Returns (warnings, errors). Never overwrites an existing external file.
    """
    warnings: List[str] = []
    errors: List[str] = []
    base = Path(paths.base_dir)
    live = Path(paths.live_unified_path)

    try:
        base.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        msg = f"Failed to create external business-rules directory {base}: {exc}"
        _LOG.error("Case Creator business rules: %s", msg)
        errors.append(msg)
        return warnings, errors

    existing_path, pick_warnings = _pick_unified_file(base)
    warnings.extend(pick_warnings)
    if existing_path is not None:
        _LOG.info(
            "Case Creator business rules: external unified file already exists at %s (no overwrite).",
            existing_path,
        )
        return warnings, errors

    if not paths.bundled_seed_path:
        msg = "No bundled seed path available in frozen mode."
        _LOG.error("Case Creator business rules: %s", msg)
        errors.append(msg)
        return warnings, errors

    seed = Path(paths.bundled_seed_path)
    if not seed.is_file():
        msg = f"Bundled unified seed missing: {seed}"
        _LOG.error("Case Creator business rules: %s", msg)
        errors.append(msg)
        return warnings, errors

    tmp_path = live.with_suffix(live.suffix + ".tmp")
    try:
        payload = seed.read_bytes()
        with tmp_path.open("wb") as f:
            f.write(payload)
        tmp_path.replace(live)
        _LOG.info(
            "Case Creator business rules: seeded external unified config from %s to %s",
            seed,
            live,
        )
    except Exception as exc:
        msg = f"Failed to seed external unified config {live} from {seed}: {exc}"
        _LOG.error("Case Creator business rules: %s", msg)
        errors.append(msg)
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except Exception:
            pass
    return warnings, errors


def _schema_defaults_effective() -> Dict[str, Dict[str, Any]]:
    return {
        "doctor_overrides": schemas.default_doctor_overrides(),
        "shade_overrides": schemas.default_shade_overrides(),
        "routing_overrides": schemas.default_routing_overrides(),
        "argen_modes": schemas.default_argen_modes(),
    }


def _defaults_preview(
    base_path: Path,
    mode: str,
    *,
    prepend_warnings: Optional[List[str]] = None,
    unified_path: Optional[Path],
    unified_validation_errors: List[str],
) -> BusinessRuleConfigPreview:
    """
    Unified file missing, unreadable, or invalid: all families use schema defaults.
    ``errors`` and ``unified_validation_errors`` carry diagnostics; ``has_errors`` is true.
    """
    effective = _schema_defaults_effective()
    diag = str(unified_path) if unified_path is not None else str(base_path / UNIFIED_RULES_FILENAMES[0])
    path_obj = Path(diag) if unified_path is not None else (base_path / UNIFIED_RULES_FILENAMES[0])
    file_exists = path_obj.is_file()

    reports: Dict[str, BusinessRuleFileReport] = {}
    for family in schemas.SUPPORTED_FAMILIES:
        reports[family] = BusinessRuleFileReport(
            family=family,
            file_path=diag,
            exists=file_exists,
            loaded=False,
            used_default=True,
            errors=[],
            warnings=["Schema defaults in use; unified business rules file missing or invalid."],
        )

    top_warnings: List[str] = list(prepend_warnings or [])
    top_warnings.append(
        "Effective business rules use schema defaults only (case_creator_rules.yaml missing or invalid)."
    )

    return BusinessRuleConfigPreview(
        base_dir=str(base_path),
        mode=mode,
        files=reports,
        effective_config=effective,
        errors=list(unified_validation_errors),
        warnings=top_warnings,
        rules_load_source="defaults",
        unified_file_path=str(unified_path) if unified_path is not None else None,
        unified_validation_errors=list(unified_validation_errors),
    )


def _load_unified_preview(
    base_path: Path,
    mode: str,
    unified_path: Path,
    raw: Dict[str, Any],
    validation: ValidationResult,
    prepend_warnings: List[str],
) -> BusinessRuleConfigPreview:
    assert validation.normalized is not None
    effective = validation.normalized
    present_families: Set[str] = set(raw.keys()) & set(schemas.SUPPORTED_FAMILIES)

    reports: Dict[str, BusinessRuleFileReport] = {}
    for family in schemas.SUPPORTED_FAMILIES:
        omitted = family not in present_families
        fam_warnings: List[str] = []
        if omitted:
            fam_warnings.append("Section omitted in unified file; defaults used.")
        reports[family] = BusinessRuleFileReport(
            family=family,
            file_path=str(unified_path),
            exists=True,
            loaded=not omitted,
            used_default=omitted,
            errors=[],
            warnings=fam_warnings,
        )

    top_warnings = list(prepend_warnings)
    top_warnings.extend(validation.warnings)

    return BusinessRuleConfigPreview(
        base_dir=str(base_path),
        mode=mode,
        files=reports,
        effective_config=effective,
        errors=[],
        warnings=top_warnings,
        rules_load_source="unified",
        unified_file_path=str(unified_path),
        unified_validation_errors=[],
    )


def load_business_rule_config_preview(override_base_dir: Optional[str] = None) -> BusinessRuleConfigPreview:
    """
    Load validated business rules from ``case_creator_rules.yaml`` (or ``.yml``).

    Split per-family YAML files are **not** read at runtime. If the unified file is missing or
    invalid, every family falls back to **schema defaults** and the preview carries errors /
    ``unified_validation_errors`` (see ``BusinessRuleConfigPreview.has_errors``).
    """
    paths = resolve_unified_runtime_paths(override_base_dir=override_base_dir)
    base_path = Path(paths.base_dir)
    mode = paths.mode

    seed_warnings: List[str] = []
    seed_errors: List[str] = []
    if mode == "frozen_windows":
        _LOG.info(
            "Case Creator business rules: frozen mode live path=%s",
            paths.live_unified_path,
        )
        seed_warnings, seed_errors = _seed_frozen_external_unified_if_missing(paths)
    if seed_errors:
        return _defaults_preview(
            base_path,
            mode,
            prepend_warnings=seed_warnings,
            unified_path=Path(paths.live_unified_path),
            unified_validation_errors=seed_errors,
        )

    unified_path, pick_warnings = _pick_unified_file(base_path)
    pick_warnings = list(seed_warnings) + list(pick_warnings)

    if unified_path is None:
        _LOG.warning(
            "Case Creator business rules: no %s in %s; load_source=defaults (schema defaults for all families).",
            " or ".join(UNIFIED_RULES_FILENAMES),
            base_path,
        )
        return _defaults_preview(
            base_path,
            mode,
            prepend_warnings=list(pick_warnings),
            unified_path=None,
            unified_validation_errors=[
                f"No unified rules file found (expected {' or '.join(UNIFIED_RULES_FILENAMES)})."
            ],
        )

    data, read_error = _read_structured_file(unified_path)

    if read_error:
        _LOG.warning(
            "Case Creator business rules: unified file %s unreadable (%s); load_source=defaults.",
            unified_path,
            read_error,
        )
        return _defaults_preview(
            base_path,
            mode,
            prepend_warnings=list(pick_warnings) + [f"Unified file read failed: {read_error}"],
            unified_path=unified_path,
            unified_validation_errors=[read_error],
        )

    assert data is not None

    validation = schemas.validate_unified_business_rules_config(data)
    if validation.valid and validation.normalized is not None:
        _LOG.info(
            "Case Creator business rules: load_source=unified path=%s",
            unified_path,
        )
        return _load_unified_preview(
            base_path, mode, unified_path, data, validation, list(pick_warnings)
        )

    err_preview = ", ".join(validation.errors[:3])
    if len(validation.errors) > 3:
        err_preview += ", ..."
    _LOG.warning(
        "Case Creator business rules: unified file %s invalid (%d error(s), e.g. %s); load_source=defaults.",
        unified_path,
        len(validation.errors),
        err_preview,
    )
    return _defaults_preview(
        base_path,
        mode,
        prepend_warnings=list(pick_warnings),
        unified_path=unified_path,
        unified_validation_errors=list(validation.errors),
    )
