# CASE CREATOR EXPANDED DOCTOR OVERRIDE FINAL PARITY REPORT

## 1. Summary of changes

- **Offline fixture** (`doctor_policy_abby_vd_offline.yaml`): Added Abby **iTero + Argen-usable shade** outcomes (`non_argen_shade: false`) for ADZ and Envision so parity covers template branches that run **before** the C3/A4 non-Argen paths (A1-style shades).
- **Parity harness** (`doctor_policy_parity_harness.py`): Expanded **offline** scenarios (Abby/VD anterior, signature, study combinations, A4 non-Argen, Abby argen-shade iTero, **non-predicate doctor abstention**, VD study+signature). Expanded **argen_modes** rows for **Envision** hints (`always_with` → modeless authoritative + abstain; `always_without` + modeless envision → match). Added **`_snapshot_parity_rows()`** driven by `tests/fixtures/doctor_policy_case_snapshots.yaml` (small, repo-local, no network).
- **No** production `doctor_overrides` seeding, **no** flag default change, **no** inline Abby/VD removal, **no** observability changes (left as in the prior pass).

## 2. Files modified

| File | Change |
|------|--------|
| `tests/fixtures/doctor_policy_abby_vd_offline.yaml` | New Abby outcomes for iTero + Argen-usable shade. |
| `tests/fixtures/doctor_policy_case_snapshots.yaml` | **New** — four snapshot entries (match + abstain). |
| `tests/doctor_policy_parity_harness.py` | New scenarios, argen envision rows, snapshot loader, summary line. |
| `CASE_CREATOR_EXPANDED_DOCTOR_OVERRIDE_FINAL_PARITY_REPORT.md` | This report (**new**). |

## 3. New parity coverage

**Offline fixture group**

- Abby **ADZ / Envision** with **iTero + A1** (Argen-usable shade).
- Non-Argen markers **A4** (Abby ADZ iTero, VD Envision iTero) alongside existing C3 coverage.
- **Anterior:** VD ADZ iTero; Abby Envision iTero — expect **no policy** (fixture abstains).
- **Signature:** VD iTero ADZ / Envision — **no policy** (code-owned signature branches).
- **Study:** Abby / VD iTero Envision — **no policy**; VD study+signature+ADZ — **no policy**.
- **Abstention:** doctor name not matching Abby/VD predicates — authoritative `argen_adzir`, policy **`None`**.

**Argen modes group**

- `always_with_contact_models` + **Envision** `argen_envision` hint (Abby & VD) → `argen_modeless_envision`, **no policy**.
- `always_without_contact_models` + **modeless Envision** hint (Abby & VD) → AI template folders, **match** fixture.

**Snapshot group** (YAML-driven)

- Mirrors a subset of the above for repeatable “case blob” checks (Abby iTero ADZ, VD C3, Abby modeless abstain, generic doctor abstain).

**Known template gap (documented, not a new failure):** For **VD**, **`select_template` currently has no branch** for **iTero + Argen-usable shade (e.g. A1)** on ADZ or Envision — it raises `ValueError`. Parity therefore does **not** add those rows; production cases like that may already be invalid or rare. Seeding live YAML must not assume parity there until `template_utils` defines behavior.

## 4. Validation performed

- `python3 tests/doctor_policy_parity_harness.py` — exit **0** (offline parity, argen parity, **4** snapshot rows, observability, flag, simple override, repo load).
- Import paths for harness dependencies unchanged; no new circular imports introduced by this pass.

## 5. Production safety

- **Default** remains: `CASE_CREATOR_DOCTOR_OUTCOMES_LIVE` off; multi-outcome rules not evaluated live unless explicitly enabled.
- This pass only touches **tests** and the **offline** parity fixture used for harness / experimentation — not `business_rules/v1/doctor_overrides.yaml` production content.

## 6. Cutover readiness assessment

**Question:** Is parity confidence now strong enough to move Abby/VD **richer rules** into **live** `doctor_overrides.yaml` in the next pass, while keeping code-owned branches as backup?

**Answer:** **Conditionally yes for a controlled next pass**, not a blanket “safe to delete code.”

- **Ready:** To **copy or mirror** the validated offline Abby/VD multi-outcome structure into **production** YAML **with the same safety model as today**: outcomes still **gated** by `CASE_CREATOR_DOCTOR_OUTCOMES_LIVE`, simple rules unchanged, inline `template_utils` logic **unchanged** as fallback and source of truth when the flag is off or when YAML abstains.
- **Not ready:** To treat parity as proof that **all** real-world Abby/VD combinations are covered, or to **remove** inline branches. Gaps remain (e.g. VD iTero + Argen shade A1, `is_ai` paths, broader study/signature grids, live shade-marker config drift).

So: **strong enough to seed live YAML for trial / parity with the flag**, **not** strong enough to declare code deletion safe.

## 7. Risks or limitations

- **template_utils** holes for some VD scanner/shade mixes (see above).
- **Fixture vs code drift** if `template_utils` changes without updating the offline YAML + harness.
- **Live shade markers** (`non_argen_shade`) can differ from defaults used in tests.
- **Argen modes** + doctor `when` must stay aligned (`excludes_modeless_hint_route` and effective hint route).

## 8. Recommended next pass

1. **Seed** production `business_rules/v1/doctor_overrides.yaml` with Abby/VD multi-outcome rules **equivalent** to the offline fixture (or a reviewed subset), **keeping the flag default off** and rolling out outcomes-live only in staging or via explicit env.
2. Add **monitoring** on `case_creator_doctor_outcomes_override` logs (from the prior pass) during any outcomes-live pilot.
3. **Follow-up:** Fix or explicitly reject VD iTero + Argen-usable shade in `template_utils` so parity and production semantics are defined.
4. Only after sustained correct behavior: plan a **separate** cleanup pass to reduce duplication (still not assumed in the near term).

---

## Final chat summary

1. **New parity coverage:** Abby iTero + A1 (ADZ/Envision), A4 non-Argen slices, more anterior/signature/study abstentions, generic-doctor abstention, Envision × argen_modes (with/without contacts + modeless envision), and a **four-row snapshot YAML** replayed by the harness.
2. **Live YAML seeding next pass:** **Reasonable with guardrails** — mirror validated rules into production file, keep **flag off by default** and code branches in place; treat as **pilot-ready**, not **delete-code-ready**.
3. **Still not safe to remove from code:** All current **inline Abby/VD** branches in `template_utils`, **label/Serbia** behavior, and undefined VD edge cases above.
4. **Safest next pass:** Seed production doctor_overrides from the reviewed fixture, enable outcomes-live only in controlled environments, monitor override logs, and fix or document VD template gaps before any de-inline effort.
