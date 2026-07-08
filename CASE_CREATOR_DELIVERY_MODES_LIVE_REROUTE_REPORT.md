# CASE CREATOR DELIVERY MODES LIVE REROUTE REPORT

> The outsource/designer delivery model is now **live**. Every case is **outsource** (Send to AI,
> zipped) by default; a case is **designer** (Send to 1.9, unzipped) only when a YAML disqualifier
> matches. The retired Argen/Serbia/Abby/VD routing no longer decides delivery.
>
> **Full test suite: 77 tests, OK.**

---

## 1. Summary of changes

- Added a single live decision, `resolve_delivery_mode(case_data)`, in the decisions layer.
  Designer is chosen **only** from YAML disqualifiers:
  - doctor → `delivery_modes.designer_doctor_names` (via `delivery_mode_runtime.is_designer_doctor`)
  - shade  → `shade_overrides.non_argen_shade_markers` (via `template_rules.is_non_argen_shade`)
- Replaced the old destination/zip decision block in `process_case` with the two-mode mapping:
  - **designer** → `SEND_TO_1_9_PATH`, `do_zip = False`
  - **outsource** (default) → `SEND_TO_AI_PATH`, `do_zip = True`
- Reused the existing zip pipeline unchanged (`zip_case_folder` + the two `if do_zip:` blocks). No
  new zip system, no new delivery engine.
- Retired the old live routing authority: removed the `select_destination` call, the
  `should_zip`/`should_zip_modeless_argen` gate, and the Argen/Serbia/AI-designer log-label
  branches from the live path.
- `has_study`, template family, and Serbia/Abby/VD no longer influence delivery.
- Updated the canonical YAML and user-facing help/prompt/README so the two-mode model is clear and
  Serbia/Abby/VD are no longer described as live delivery behavior.
- Housekeeping: added `.gitignore` and untracked committed `__pycache__/*.pyc` + `.DS_Store` noise.

---

## 2. Files modified

**Live code**
- `domain/decisions/delivery_mode_selector.py` **(new)** — `resolve_delivery_mode()` +
  `MODE_OUTSOURCE` / `MODE_DESIGNER`.
- `case_processor_final_clean.py`
  - Imports: replaced `from domain.decisions.destination_selector import select_destination` with
    `from domain.decisions.delivery_mode_selector import resolve_delivery_mode, MODE_DESIGNER`;
    dropped the now-unused `SEND_TO_ARGEN_PATH` import.
  - Removed the dead `should_zip(...)` function (its Argen-zip gate is retired).
  - Replaced the destination/zip decision block
    ([case_processor_final_clean.py:469-483](case_processor_final_clean.py:469)) with the two-mode
    mapping.

**Canonical config + seed**
- `business_rules/v1/case_creator_rules.yaml` — added a delivery-model header comment; clarified
  that `doctor_overrides` is template-only (not delivery); marked `delivery_modes` LIVE. Rules
  content unchanged (comments only).
- `business_rules_seed/v1/case_creator_rules.yaml` — synced (byte-parity kept).

**User-facing docs**
- `business_rules/v1/README.md` — rewritten around the outsource/designer model; Serbia removed.
- `business_rules/v1/CASE_CREATOR_RULES_EDIT_PROMPT.md` — replaced the "destination vs label"
  section with a "DELIVERY MODEL" section; marked `delivery_modes` live; reframed `doctor_overrides`
  as template-only; removed Serbia/route-label-as-delivery instructions and examples.

**Tests / housekeeping**
- `tests/test_delivery_mode_live_reroute.py` **(new)** — decision + end-to-end wiring tests.
- `.gitignore` **(new)** — `__pycache__/`, `*.py[cod]`, caches, `.DS_Store`.
- Untracked previously-committed `*.pyc` (67) and `.DS_Store` via `git rm --cached` (working copies
  retained).

---

## 3. New live delivery decision model

`domain/decisions/delivery_mode_selector.py`:

```python
def resolve_delivery_mode(case_data) -> str:
    doctor = (case_data or {}).get("doctor", "") or ""
    shade  = (case_data or {}).get("shade", "") or ""
    if is_designer_doctor(doctor):      # delivery_modes.designer_doctor_names (case-insensitive substring)
        return MODE_DESIGNER
    if is_non_argen_shade(shade):       # shade_overrides.non_argen_shade_markers (existing live behavior)
        return MODE_DESIGNER
    return MODE_OUTSOURCE               # default for all cases
```

Live mapping in `process_case` ([case_processor_final_clean.py:473-483](case_processor_final_clean.py:473)):

| Mode | Condition | `target_root` | `do_zip` | Effect |
| --- | --- | --- | --- | --- |
| `designer` | doctor or shade disqualifier matches | `SEND_TO_1_9_PATH` | `False` | Send to 1.9, **unzipped** |
| `outsource` | default (everything else) | `SEND_TO_AI_PATH` | `True` | Send to AI, **zipped** |

The existing `zip_case_folder()` and both `if do_zip:` blocks (non-3Shape and 3Shape branches) are
reused unchanged — outsource now exercises them; designer skips them.

---

## 4. Old routing authority retired

Removed from the **live** path (no longer invoked by `process_case`):

- **`select_destination(...)`** — previously produced `destination_key` (argen / 1_9) and
  `route_label_key` (including `serbia`, `designer`, `ai_designer`, `ai_serbia`) and applied
  doctor route-label overrides. No longer called (verified: no live reference remains).
- **`should_zip` / `should_zip_modeless_argen`** — the modeless-Argen zip gate. The local
  `should_zip` wrapper was deleted; zip is now decided by delivery mode.
- **Serbia / Argen / AI-designer log-label branches** — removed; replaced by a single
  `DESIGNER CASE` / `OUTSOURCE CASE` log line.
- **`SEND_TO_ARGEN_PATH`** — no longer a live delivery target (import dropped). The folder is still
  created by `config.py`, but nothing routes to it.
- **Doctor-overrides delivery authority** — because `select_destination` is no longer called,
  `doctor_overrides` (incl. Abby/VD and any `route_label_override_key`) no longer influences
  delivery. Per the brief, `doctor_overrides` remains available for **template selection only**
  (env-gated by `CASE_CREATOR_DOCTOR_OUTCOMES_LIVE`, default off) and was left otherwise unchanged.

Retained on disk as **dormant library code** (present but uninvoked, for rollback/parity — not live
authority): `domain/decisions/destination_selector.py`, and the
`routing_rules` helpers (`is_serbia_case`, `route_label_for_template`, `LABEL_SERBIA`,
`should_zip_modeless_argen`, destination keys). Template selection (`select_template_path` /
`select_template`) was intentionally **not** changed.

---

## 5. YAML changes

- **`delivery_modes.designer_doctor_names`** is now the live, single source of truth for
  doctor-based designer exclusion. Left as `[]` (operator populates; no doctor is presumed
  designer). Comment updated from "dormant" to live, with a `Brier Creek` example.
- **`shade_overrides.non_argen_shade_markers`** remains the live source of truth for shade-based
  designer exclusion (unchanged; still `C3`, `A4`).
- Added a **delivery-model header** to the canonical file (outsource default → Send to AI zipped;
  designer exception → Send to 1.9 unzipped; `has_study` does not decide).
- Added a note that **`doctor_overrides` no longer controls delivery** (template-only). Its rule
  content was **not** modified (comments only), so unified-config normalized parity is preserved.
- `README.md` and `CASE_CREATOR_RULES_EDIT_PROMPT.md` rewritten/edited to teach: default =
  outsource; excluded doctors/shades = designer; **no Serbia**; **no Abby/VD special delivery**.

---

## 6. Validation / tests performed

- **New `tests/test_delivery_mode_live_reroute.py`:**
  - Decision (`resolve_delivery_mode`, hermetic injected config): default → outsource; excluded
    doctor → designer; excluded shade (incl. vita-prefixed) → designer; `has_study` true/false does
    **not** flip mode; `Abby Dew` / `VD Brier Creek` with an empty list → outsource, and →
    designer **only** when explicitly listed.
  - End-to-end wiring (real `process_case`, seams stubbed): default case → **zipped in Send to AI**,
    unzipped folder removed, nothing in designer; excluded doctor → **unzipped folder in Send to
    1.9**, no zip; excluded shade → **unzipped in Send to 1.9**.
- **Full suite:** `Ran 77 tests ... OK` (69 prior + 8 new).
- Canonical loads as `rules_load_source="unified"`, `has_errors=False`; canonical ↔ seed byte
  parity verified; comment-only YAML edits keep all normalized-parity tests green.

---

## 7. Risks or limitations

1. **`doctor_overrides` Abby/VD rules remain in the canonical YAML** (template-only, env-gated off).
   They were intentionally not purged to avoid changing template behavior and breaking the
   split→unified migration-parity tests. They no longer affect delivery. A later template-focused
   pass can remove them and retire those parity tests.
2. **`Send to AI` is now an active zipped destination.** Confirm the downstream consumer accepts the
   `zip_case_folder` shape (folder as the single top-level entry) — this is the same shape the
   Argen zip path historically produced.
3. **Designer folder assumption:** designer maps to `SEND_TO_1_9_PATH` per the confirmed decision. If
   the designer team watches a different physical folder, it is a one-line change.
4. **3Shape outsource cases now zip** via the existing 3Shape `if do_zip:` block; the end-to-end
   test exercised the non-3Shape branch. Worth a real 3Shape smoke test.
5. **Dormant leftovers:** `SEND_TO_ARGEN_PATH` is still created by `config.py`;
   `destination_selector` and the Serbia/zip `routing_rules` helpers remain uninvoked. Harmless, but
   they are dead code until a cleanup pass.
6. **Config caching:** delivery mode reads config once per process (`@lru_cache`), consistent with
   the documented "save and restart" workflow.
7. **Shade timing:** the decision reads `case_data["shade"]` before XML shade-cleaning; the match is
   uppercase substring and tolerates vita prefixes (tested), matching prior `is_non_argen_shade`
   semantics.

---

## 8. Recommended next pass

Optional, conservative cleanup (separate pass — not required for correctness):

1. Retire dormant code now that it is uninvoked: `domain/decisions/destination_selector.py`, the
   Serbia/zip helpers in `routing_rules`, and stop creating `SEND_TO_ARGEN_PATH` in `config.py`.
2. Decide the fate of `doctor_overrides` Abby/VD rules (template-only). If template selection no
   longer needs them, remove them and update/retire the split→unified migration-parity tests that
   assert canonical == archived baseline.
3. If the business wants specific doctors (e.g. VD Brier Creek) delivered to the designer, add them
   to `delivery_modes.designer_doctor_names`.
4. Add a real 3Shape outsource smoke test and confirm the `Send to AI` consumer's zip expectations.
