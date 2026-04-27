# 1. Duplicate Tree Inventory

Status note:
- Root tree is the intended canonical codebase.
- Nested tree should be treated as legacy and retired via manual soft-retirement steps (see `DUPLICATE_RETIREMENT_PLAN.md`).

## Identified trees

- **Root/front tree:** `/Users/bretthoffman/Documents/3shape_case_importer`
- **Nested duplicate tree:** `/Users/bretthoffman/Documents/3shape_case_importer/3shape_case_importer`

## What is duplicated

A file-level hash comparison was run between:
- root tree files (excluding the nested subtree itself), and
- nested tree files.

Results:
- Root files: **80**
- Nested files: **79**
- Common relative paths: **79**
- Identical-by-content: **72**
- Different-by-content: **7**
- Root-only: **1** (`CODEBASE_AUDIT.md`)
- Nested-only: **0**

## Duplicated file families (present in both trees)

### Runtime code files

- `import_gui.pyw`
- `case_processor_final_clean.py`
- `template_utils.py`
- `config.py`
- `evo_internal_client.py`
- `evo_to_case_data.py`
- `evolution_case_detail.py`
- `manual_import.py`
- `rx_fetch_and_parse.py`
- `evo_terminal_probe.py`
- `test_evo_request.py`
- `launch_importer.bat`
- `requirements.txt`

### Runtime data/assets

- `templates/*` (16 template folders with XML + `Materials.xml` + `Manufacturers.3ml`)
- `cc imported cases/*` route folders
- `List of Signature Dr.xlsx`
- `dr prefs.xml`
- `case_creator_icon.ico`
- `python-3.13.3-amd64.exe`

### Non-source cache/artifacts

- `__pycache__/*` exists in both trees (not canonical source; machine/runtime-generated).


# 2. Runtime Entry Determination

## Most likely launched tree on this machine

**Most likely root tree**, based on launcher behavior:

- Both `launch_importer.bat` files (root and nested) contain:
  - `set "PROJECT_DIR=C:\Users\brett\Documents\3shape_case_importer"`
  - `pushd "%PROJECT_DIR%"`
  - `py -w import_gui.pyw` / `pythonw import_gui.pyw`

This means the launcher forces execution from the project root path, then runs `import_gui.pyw` from that directory.

## Entry indicators reviewed

- Launcher: `launch_importer.bat` (both copies)
- UI entry: `import_gui.pyw`
- Backend import in UI: `from case_processor_final_clean import process_case_from_id as process_case`
- No package-qualified imports like `from 3shape_case_importer...` found.
- No `sys.path` mutation or dynamic import path redirection found.

## Uncertainty / not fully provable

Cannot fully prove all runtime scenarios from repository inspection alone. Possible edge cases:
- A user may manually run `pythonw 3shape_case_importer/import_gui.pyw` directly.
- A machine shortcut/external scheduler could target nested files directly.
- Environment differences on other machines may bypass `launch_importer.bat`.

So: root is the **primary expected runtime**, but nested could still be used in ad-hoc/manual launch paths.


# 3. Drift Comparison

## Overall drift status

Trees are **near-duplicate but not perfectly identical**.  
Substantive source drift exists in `config.py`; minor text drift exists in `import_gui.pyw`.

## Content differences found

### Behavior-sensitive drift

1. `config.py` (root vs nested)
   - `TRIOS_SCAN_ROOT`: `A:\...New Dec 25` (root) vs `X:\...New` (nested)
   - `SIGNATURE_DOCTORS_PATH`: different username path (`kkollarova` vs `brett`)
   - `TEMPLATE_DIR`: different username path (`kkollarova` vs `brett`)
   - `CC_IMPORTED_ROOT`: `A:\cc imported cases` (root) vs `X:\cc imported cases` (nested)

**Impact:** high. This can change input scan source, template source, and output destination roots.

2. `import_gui.pyw`
   - Subheader text differs:
     - root: `Kat's Single-Unit Scraper`
     - nested: `Kat's Single Unit Scraper`

**Impact:** UI text only (non-behavioral for processing/output).

### Non-source drift

`__pycache__` files differ in hash/size/timestamps (expected and not behavior-authoritative source code).

## Timestamp drift

Timestamp differences were observed in 8 files (including `config.py`, `import_gui.pyw`, one matching code file, and multiple `.pyc` files).  
Given identical hashes for most source files, timestamp drift alone does not imply behavior drift, but confirms trees were edited/loaded at different times.

## Presence/absence drift

- Root-only: `CODEBASE_AUDIT.md`
- Nested-only: none

## Conclusion on identity

The trees are **not strictly identical** due to `config.py` and one UI string.  
Core processing scripts/templates are otherwise identical by content in this snapshot.


# 4. Dependency / Import Risk

## Do imports reference nested tree directly?

No direct nested-tree imports detected:
- no `import 3shape_case_importer...`
- no `from 3shape_case_importer...`
- no `sys.path` adjustments pointing to nested subtree.

Current imports are simple local-module imports (`from case_processor_final_clean ...`, `from config ...`), resolved by current working directory/module path.

## Removal risks if nested tree is deleted prematurely

Potential break scenarios:
- Any external shortcut/script pointing directly to nested `import_gui.pyw`.
- Any workflow that `cd`s into nested tree and runs scripts from there.
- Any machine whose effective `config.py` values currently depend on nested copy’s different paths (notably `X:` vs `A:` roots).

## Relative path / template loading assumptions

- Template location is absolute via `TEMPLATE_DIR` in `config.py`, not relative.
- Therefore, import target tree determines which `config.py` is loaded and thus which absolute paths are used.
- Removing nested tree is likely safe **only if all launch paths are confirmed to use root tree config**.


# 5. Safe Canonical Tree Recommendation

## Recommendation

Use the **root/front tree** (`/Users/bretthoffman/Documents/3shape_case_importer`) as canonical.

## Why

- Launcher explicitly targets root project path.
- Root contains newest project-level audit/doc artifacts.
- Root is the natural repository/workspace top-level.
- Keeping root canonical aligns with current batch startup assumptions.

## Caveat

Because nested `config.py` differs in path roots and user-path values, canonicalization should only proceed after machine-by-machine launch verification.


# 6. Safe Removal Plan

## Phase 0 - No behavior changes

1. Do not delete/move either tree yet.
2. Freeze both trees from opportunistic edits during verification window.

## Phase 1 - Prove launch path

3. On each production machine, confirm actual startup target:
   - inspect shortcut target / startup task command,
   - verify it calls root `launch_importer.bat` (or root `import_gui.pyw`).
4. Add temporary startup logging (path-only, no logic change) in a controlled test build:
   - log `__file__`, cwd, and loaded `config.py` path.
   - run one import and capture evidence.

## Phase 2 - Prove functional redundancy

5. Compare root vs nested file manifests on each machine:
   - common files hash-equal except known intentional drift.
6. Run representative imports through confirmed root launch path and validate outputs against expected baselines.
7. Specifically verify path-sensitive behavior (`TRIOS_SCAN_ROOT`, `CC_IMPORTED_ROOT`, template path source) is correct under root config.

## Phase 3 - De-risk before deletion

8. Create a full backup/archive snapshot of nested tree (read-only archive).
9. Rename nested tree first (soft retirement), e.g. `3shape_case_importer__retired_candidate` (later phase, not now), then run smoke tests.
10. If no breakage during monitoring window, delete retired copy.

## Verification checklist before final deletion

- Root launcher used in all startup points.
- No external script/shortcut references nested paths.
- One full import pass per scanner family succeeds.
- Output XML/file trees match baseline expectations.
- No runtime import/load failures after nested tree quarantine.


# 7. Do Not Change Yet

Do **not** automatically change any of the following at this stage:

- Do not delete `3shape_case_importer/`.
- Do not move files between trees.
- Do not refactor imports to package-qualified paths.
- Do not merge/normalize `config.py` values yet.
- Do not alter template directories or template filenames.
- Do not change launcher behavior until startup targets are proven on all machines.
- Do not touch processing logic (`case_processor_final_clean.py`, `template_utils.py`, `evo_to_case_data.py`) as part of duplicate cleanup.

Current safe action is documentation + verification only.

