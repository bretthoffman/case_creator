from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class BusinessRuleFileReport:
    family: str
    file_path: str
    exists: bool
    loaded: bool
    used_default: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class BusinessRuleConfigPreview:
    base_dir: str
    mode: str
    files: Dict[str, BusinessRuleFileReport]
    effective_config: Dict[str, Dict[str, Any]]
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    # rules_load_source: "unified" (case_creator_rules valid) or "defaults" (missing/invalid unified).
    rules_load_source: str = "defaults"
    unified_file_path: Optional[str] = None
    unified_validation_errors: List[str] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return bool(self.errors) or any(r.errors for r in self.files.values())

    @property
    def has_warnings(self) -> bool:
        return bool(self.warnings) or any(r.warnings for r in self.files.values())


@dataclass(frozen=True)
class UnifiedRuntimePaths:
    mode: str
    base_dir: str
    live_unified_path: str
    bundled_seed_path: Optional[str] = None


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    normalized: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
