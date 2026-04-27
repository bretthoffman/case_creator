# CASE CREATOR UNIFIED CONFIG CANONICAL CLEANUP REPORT

## 1. Summary of changes

The repo now treats **`business_rules/v1/case_creator_rules.yaml`** as the **single canonical human-edited** unified rules file. **`business_rules_seed/v1/case_creator_rules.yaml`** is documented and maintained as a **bundled default seed** only: it is kept **byte-identical** to the canonical file via `scripts/sync_unified_config_seed.py` and automatically refreshed from canonical **before PyInstaller** in `scripts/windows/build_pyside6_onefolder.bat`.

An operator-facing guide was added at **`business_rules/v1/README.md`** (what can be edited, packaged vs dev paths, examples). The canonical YAML header comments now state the canonical vs seed vs packaged-external relationship.

## 2. Files modified

| Action | Path |
|--------|------|
| Created | `scripts/sync_unified_config_seed.py` |
| Created | `business_rules/v1/README.md` |
| Created | `tests/test_unified_canonical_seed_parity.py` |
| Created | `CASE_CREATOR_UNIFIED_CONFIG_CANONICAL_CLEANUP_REPORT.md` (this file) |
| Modified | `business_rules/v1/case_creator_rules.yaml` (header comments only) |
| Modified | `business_rules_seed/v1/case_creator_rules.yaml` (refreshed via sync; matches canonical) |
| Modified | `scripts/windows/build_pyside6_onefolder.bat` (copy canonical → seed before build) |
| Modified | `docs/packaging/PYINSTALLER_BUILD_PLAN.md` (seed + sync documentation) |
| Modified | `docs/packaging/PACKAGED_UNIFIED_CONFIG_FRESH_PROFILE_SMOKE_TEST.md` (prerequisites note) |

## 3. Canonical file decision

**Human-edited source of truth in the repo:**  
`business_rules/v1/case_creator_rules.yaml`

## 4. Seed handling

- **Development:** After editing the canonical file, run:
  - `python3 scripts/sync_unified_config_seed.py`
- **Windows packaged build:** `scripts/windows/build_pyside6_onefolder.bat` copies canonical → `business_rules_seed/v1/case_creator_rules.yaml` before invoking PyInstaller (runtime contract unchanged).
- **Parity guard:** `tests/test_unified_canonical_seed_parity.py` asserts canonical and seed files are byte-identical so the two paths cannot drift unnoticed.

## 5. README/guidance changes

**`business_rules/v1/README.md`** now covers:

- Single file to edit in-repo vs seed vs `%LOCALAPPDATA%` after install  
- Save + restart  
- Plain-English description of **doctor**, **shade**, **routing**, and **argen** sections  
- What **not** to put in YAML (paths, scanner internals, etc.)  
- Example snippets (simple doctor rule, contact model on, shade marker, routing row)

## 6. Validation performed

- `diff` / byte parity: canonical and seed matched before header edit; after edits, `python3 scripts/sync_unified_config_seed.py` was run to re-align seed.
- `python3 -m unittest tests.test_unified_canonical_seed_parity tests.test_business_rule_loader_dual_read -q` — passed.
- No changes to `business_rule_schemas.py`, resolvers, or loader validation logic beyond prior behavior.

## 7. Risks or limitations

- Contributors must run the sync script (or a release build) after changing the canonical file, or the parity test will fail — this is intentional drift protection.
- Non-Windows packaging flows, if added later, must also copy canonical → seed or call the same sync step.

## 8. Final operator guidance

- **In the repo:** edit **`business_rules/v1/case_creator_rules.yaml`** only (see **`business_rules/v1/README.md`**).
- **Do not** maintain **`business_rules_seed/v1/case_creator_rules.yaml`** as a separate hand-edited source.
- **On a packaged PC:** edit **`%LOCALAPPDATA%\CaseCreator\business_rules\v1\case_creator_rules.yaml`** for that installation.

---

## Final chat summary

1. **Canonical human-edited file:** `business_rules/v1/case_creator_rules.yaml`
2. **Packaged seed:** `business_rules_seed/v1/case_creator_rules.yaml` is refreshed from canonical via `scripts/sync_unified_config_seed.py` and the Windows build script before packaging.
3. **Runtime behavior:** Unchanged (comments + docs + sync/parity only; schema and loader logic untouched).
4. **README for operators:** `business_rules/v1/README.md` points editors to the canonical file and explains editable areas and examples.
