# CASE CREATOR BASELINE YAML VALIDATION REPORT

> Validation + finalization pass. No new features, no routing redesign, no template-selection
> changes, no updater changes. Only comment-level documentation was added to the canonical YAML and
> focused validation tests were added. **Full test suite: 94 tests, OK.**

---

## 1. Summary of findings

- **A — Does any legacy YAML still interfere with delivery? No.** The live delivery decision is made
  solely by `resolve_delivery_mode(case_data)`, which reads **only**
  `delivery_modes.designer_doctor_names` and `shade_overrides.non_argen_shade_markers`.
  `doctor_overrides`, `routing_overrides`, and `argen_modes` are **dormant for delivery** — they can
  influence template selection / XML only, never where a case is delivered or whether it is zipped.
  Verified by consumer tracing and a new isolation test.
- **B — Is outsource definitely zipped in the live path? Yes.** Outsource sets `do_zip = True` and
  `target_root = SEND_TO_AI_PATH`; both scanner branches then call the existing `zip_case_folder()`
  and delete the unzipped folder. Designer sets `do_zip = False` and stays unzipped. Proven by
  existing end-to-end tests.
- **C — Is the canonical YAML safe to ship as the baseline? Yes**, with one conscious, documented
  default: the shipped `non_argen_shade_markers: [C3, A4]` are **active** designer exclusions (C3/A4
  cases go to the designer). `designer_doctor_names` is empty, so no doctor is forced to designer.
  No legacy field can accidentally force designer or cancel the model.

The baseline needed no value changes. This pass added clarifying comments (legacy/dormant markers,
and an explicit note that the C3/A4 shade defaults are active) and validation tests.

---

## 2. Files modified

- `business_rules/v1/case_creator_rules.yaml` — **comments only** (no value/structure changes):
  - `routing_overrides`: marked LEGACY / dormant; does not affect delivery.
  - `argen_modes`: marked LEGACY / dormant; template/XML only; leave off.
  - `shade_overrides`: added a note that the shipped `C3`/`A4` defaults are **active** designer
    exclusions and can be emptied if those shades should stay outsource.
- `business_rules_seed/v1/case_creator_rules.yaml` — re-synced (byte-parity kept).
- `tests/test_baseline_delivery_isolation.py` — **new** focused validation tests.

No application/runtime code was changed in this pass.

---

## 3. Legacy YAML / config audit

Live consumer trace (who actually reads each family, and whether it can affect delivery):

| Family | Live consumer(s) | Affects delivery? | Verdict |
| --- | --- | --- | --- |
| `delivery_modes.designer_doctor_names` | `delivery_mode_runtime.is_designer_doctor` → `resolve_delivery_mode` | **Yes (authoritative)** | Live doctor exclusion |
| `shade_overrides.non_argen_shade_markers` | `template_rules.is_non_argen_shade` → `resolve_delivery_mode` **and** `template_utils.select_template` | **Yes (authoritative)** + template selection | Live shade exclusion (shared) |
| `doctor_overrides` | `template_selector` (template override, env-gated) and `destination_selector` (not called live) | No | Dormant for delivery; `rules: []` |
| `routing_overrides` | `routing_override_runtime.resolve_destination_key` → `select_destination` (**not called live**) | No | Dormant for delivery |
| `argen_modes` | `template_rules.contact_model_argen_on` (template select) + `generate_final_xml` (XML value) | No | Dormant for delivery; `off` |

Key points:
- `select_destination` / `resolve_destination_key` (the only consumers of `routing_overrides`) are
  **no longer called** by `process_case` (removed in the live-reroute pass; confirmed by grep — only
  the module itself and tests reference them). So `routing_overrides` has **zero** delivery effect.
- `doctor_overrides.rules` is empty, and even a populated rule only yields a *template* override
  (env-gated), never a delivery change.
- `argen_modes` is `off`; even turned `on` it only selects `argen_modeless_*` templates — delivery
  is still decided by `resolve_delivery_mode`.
- **Nothing can cancel or override** the outsource/designer decision: the processor maps the mode
  straight to `(target_root, do_zip)` with no other conditions.

**Conflict found:** none. The only legacy content that changes delivery from a pure-outsource
default is the `shade_overrides.non_argen_shade_markers` defaults `C3`/`A4` — and that is the
**intended, documented** shade-exclusion mechanism (not a stray value), so it is kept.

New isolation test `tests/test_baseline_delivery_isolation.py` proves this: with `doctor_overrides`
populated, `routing_overrides` set to `ai → argen`, and `argen_modes` on — but the two exclusion
fields empty — a normal case still resolves to **outsource**; designer occurs **only** via the two
exclusion fields.

---

## 4. Live outsource zip verification

Live path in `case_processor_final_clean.py`:

```python
delivery_mode = resolve_delivery_mode(case_data)              # line 473
if delivery_mode == MODE_DESIGNER:
    target_root = SEND_TO_1_9_PATH ; do_zip = False           # designer -> unzipped
else:  # MODE_OUTSOURCE (default for all cases)
    target_root = SEND_TO_AI_PATH  ; do_zip = True            # outsource -> zipped
```

Both scanner branches reuse the existing zip pipeline:

```python
if do_zip:                                                    # lines 581 and 601
    zip_path = zip_case_folder(final_output, log_callback)    # zip_case_folder def at line 43
    shutil.rmtree(final_output)                               # remove unzipped folder
    return f"Completed {case_id} → {zip_path}"
return f"Completed {case_id} → {final_output}"                # unzipped (designer)
```

- **Confirmed:** outsource reaches `zip_case_folder`; designer does not.
- **Existing tests prove it** (no new tests needed here) —
  `tests/test_delivery_mode_live_reroute.py::TestProcessCaseDeliveryWiring`:
  - `test_default_case_outsource_zipped_send_to_ai` — exactly one `.zip` in **Send to AI**, no
    leftover unzipped folder, nothing in the designer folder.
  - `test_excluded_doctor_designer_unzipped_send_to_1_9` — an unzipped folder in **Send to 1.9**, no
    zip.
  - `test_excluded_shade_designer_unzipped_send_to_1_9` — same, via a shade exclusion.

---

## 5. Final recommended shipped baseline YAML state

Ship the current canonical **as-is** (values below; comments added this pass):

| Family | Shipped value | Rationale |
| --- | --- | --- |
| `doctor_overrides` | `enabled: true`, `rules: []` | Empty. Dormant for delivery; template-only. Safe. |
| `shade_overrides` | `non_argen_shade_markers: [C3, A4]`, `rules: []` | **Active** shade exclusion → C3/A4 go to designer. Kept because it is the documented mechanism **and** is shared with template selection (emptying it would change template selection, which is out of scope). |
| `routing_overrides` | 4 legacy family→dest mappings | Dormant for delivery (uninvoked). Kept for compatibility; commented as legacy. |
| `argen_modes` | `contact_model_mode: off`, `contact_model_design_field: 3Shape Automate` | Dormant for delivery; off. Kept; commented as legacy. |
| `delivery_modes` | `designer_doctor_names: []` | Empty → no doctor forced to designer. Correct, beginner-safe default. |

Net delivery behavior of the shipped baseline: **every case is outsource (Send to AI, zipped)
except cases whose shade is C3 or A4 (→ designer, Send to 1.9, unzipped)**. This is locked by
`tests/test_baseline_delivery_isolation.py::TestShippedBaselineDeliveryBehavior`.

If the business wants a **zero-exception** outsource baseline, the only change is
`non_argen_shade_markers: []` — but note that also removes C3/A4 from `select_template`'s
non-Argen-shade branch, changing which template file those cases use (a template-selection change,
deliberately not made here).

---

## 6. Validation / tests performed

- **Consumer trace** (grep) confirming `resolve_delivery_mode` is the sole delivery authority and
  that `select_destination`/`resolve_destination_key` are uninvoked live.
- **New** `tests/test_baseline_delivery_isolation.py`:
  - legacy families populated + empty exclusions → **outsource**; designer only via exclusion fields.
  - shipped canonical → normal case **outsource**; C3/A4 → **designer** (locks the shipped default).
- **Existing** `tests/test_delivery_mode_live_reroute.py` — outsource zipped / designer unzipped
  end-to-end (pointed to, not duplicated).
- Canonical loads as `rules_load_source="unified"`, `has_errors=False`; comment-only edits leave all
  normalized-parity tests green; canonical ↔ seed **byte parity** verified.
- **Full suite: `Ran 94 tests ... OK`.**

---

## 7. Remaining risks or limitations

1. **C3/A4 ship as active designer exclusions.** This is intended and documented, but it is a
   product decision: fresh installs send C3/A4 shade cases to the designer. Empty the list if that
   is not desired (with the template-selection caveat above).
2. **Shade matching is substring, case-insensitive** (pre-existing semantics, intentionally
   unchanged). With the shipped `C3`/`A4` this does not over-match any real Vita shade (e.g. `A4` is
   not a substring of `A3.5`). Documented for awareness; not a defect introduced here.
3. **Dormant legacy families remain present** (`doctor_overrides` plumbing, `routing_overrides`,
   `argen_modes`, and uninvoked `select_destination`/`should_zip_modeless_argen`). Harmless and kept
   for compatibility/rollback; a future code pass could remove them.
4. **Config is cached per process** (`@lru_cache`); edits apply on app restart, matching the
   documented "save and restart" workflow.

---

## 8. Recommended next step

- **Ship the current canonical as the release baseline** — it is already synced to
  `business_rules_seed/v1/case_creator_rules.yaml` (byte-parity verified), which is what packaged
  installs seed from on first run.
- Before tagging the release, get an explicit product yes/no on the **C3/A4 → designer** default. If
  "no", set `non_argen_shade_markers: []` (a one-line, comment-guided edit) and re-run
  `scripts/sync_unified_config_seed.py`.
- No code changes are required for release; delivery behavior is validated and test-locked.
