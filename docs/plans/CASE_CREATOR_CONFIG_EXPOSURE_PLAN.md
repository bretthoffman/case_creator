CASE CREATOR CONFIG EXPOSURE PLAN

## 1. Purpose

Case Creator is now at the right planning point for config exposure because the highest-risk business rules have been centralized (or have explicit seams) rather than scattered across UI, processor, and helper files. That centralization makes it possible to expose controlled business policies without exposing engine internals.

Config exposure should happen **after** rule centralization because:
- rule ownership is clearer,
- validation boundaries are clearer,
- default/fallback behavior can map to one place per rule family,
- behavior-preserving rollout is feasible.

---

## 2. Config Exposure Goals and Non-Goals

### Goals
- Allow safe edits to selected business policies without source-code edits.
- Preserve packaged app runtime stability while allowing post-package rule updates.
- Keep current behavior as the default baseline when no business-rule config is present/valid.
- Use centralized rule modules as the single runtime readers of business-rule config.
- Support future editing via the existing settings/admin surfaces (incrementally), without introducing a new dashboard stack.

### Non-goals
- Exposing all rule families immediately.
- Exposing scanner/file-system heuristics broadly in phase 1.
- Replacing existing path/settings (`local_settings.json` / `admin_settings.json`) with business-rule config.
- Rewriting template precedence engine as a rule-table now.
- Letting malformed config crash imports/startup.

---

## 3. Recommended First Exposed Rule Families

### Expose now (phase 1)

1. **Doctor keyword override rules**
   - Why strong candidate: business-driven, frequent operational exceptions.
   - Why safer: mostly string matching + route/template key outcomes.
   - Supports: “if doctor name contains X, force template family Y” or “route label override.”

2. **Shade override/exception rules (narrow subset)**
   - Why strong candidate: business policy shifts (e.g., what counts as non-Argen shade).
   - Why safer: can expose simple allow/deny lists first, keep conversion internals code-owned.
   - Supports: changing shade exception sets without editing code.

3. **Routing override rules (key-based, not path-based)**
   - Why strong candidate: destination behavior changes operationally over time.
   - Why safer: expose route keys only (`argen`, `1_9`, etc.), keep path resolution internal.
   - Supports: controlled template-family-to-route overrides.

4. **Argen/contact-model mode toggles (limited)**
   - Why strong candidate: explicit business mode shifts expected.
   - Why safer: expose constrained booleans/enums, not full branch rewrites.
   - Supports: enabling/disabling specific mode behavior without code edits.

5. **Template override mappings (bounded)**
   - Why strong candidate: targeted policy overrides.
   - Why safer: explicit scoped overrides with strict keys and precedence position constraints.
   - Supports: template-key remaps for specific business cases.

### Expose later (phase 2+)

6. **Material keyword mappings**
   - Valuable but higher risk due to route/material extraction coupling and wording ambiguity.

7. **Manual-review gate rules**
   - Valuable but sensitive because early returns/messages are behavior-critical.

8. **Naming/suffix rules**
   - Lower urgency; behavior is stable and technical coupling is moderate.

### Keep internal for now

9. **Scanner keyword rules and heuristics**
   - Keep internal initially; high fragility and filesystem interaction.
   - Revisit after broader rule-config stabilization and stronger validation UX.

---

## 4. Proposed Config Architecture

### Core architecture
- Keep existing operational settings architecture unchanged:
  - `local_settings.json` for paths/UI prefs,
  - `admin_settings.json` for credentials/admin values.
- Add a separate **business-rule config layer** for editable policy only.
- Runtime resolution order for business policy:
  1) hardcoded defaults in rule modules (authoritative baseline),
  2) optional external business-rule files,
  3) validated merge/override into in-memory rule state.

### Location strategy
- Editable business rules should live outside packaged binaries for post-package edits.
- Use app data directory in frozen Windows mode (same root family as current settings):
  - `%LOCALAPPDATA%\CaseCreator\business_rules\...`
- In source/dev mode:
  - repo-local `business_rules/` folder (or optional mirror path), with identical file layout.

### File strategy
- Multiple small files (by rule family) is safer than one mega file:
  - narrower blast radius,
  - easier validation/errors,
  - easier phased rollout.

### Defaults strategy
- Defaults remain in code first.
- Optional starter JSON files can be generated/copied to editable location.
- If files are missing/invalid, runtime falls back to code defaults.

---

## 5. Proposed Config File Structure

Recommended phase-structured layout:

```text
business_rules/
  v1/
    doctor_overrides.json
    shade_overrides.json
    routing_overrides.json
    argen_modes.json
    template_overrides.json
```

### `doctor_overrides.json` (phase 1)
- Contains: doctor keyword/group override rules (scoped outcomes).
- Does not contain: filesystem paths, credentials, raw template XML paths.

### `shade_overrides.json` (phase 1 narrow)
- Contains: exposed shade exception sets and optional override actions.
- Does not contain: full conversion engine internals initially.

### `routing_overrides.json` (phase 1)
- Contains: route-key overrides by template family/conditions.
- Does not contain: absolute output directories.

### `argen_modes.json` (phase 1)
- Contains: constrained Argen mode toggles/selectors.
- Does not contain: deep branch rewrites or free-form scripts.

### `template_overrides.json` (phase 1 limited)
- Contains: bounded template-key remaps.
- Does not contain: arbitrary precedence graph edits.

### Later-phase candidates
- `material_mappings.json` (phase 2)
- `manual_review_overrides.json` (phase 2)
- `naming_overrides.json` (phase 3, optional)
- Scanner config file should remain deferred.

---

## 6. Proposed Data Shapes

### Doctor override rules

```json
{
  "version": 1,
  "enabled": true,
  "rules": [
    {
      "id": "abby_dew_template_override",
      "enabled": true,
      "match": {
        "contains_all": ["abby", "dew"]
      },
      "action": {
        "template_override_key": "ai_adzir"
      }
    },
    {
      "id": "brier_creek_route_label",
      "enabled": true,
      "match": {
        "contains_any": ["brier creek"]
      },
      "action": {
        "route_label_override_key": "serbia"
      }
    }
  ]
}
```

### Shade override rules

```json
{
  "version": 1,
  "enabled": true,
  "non_argen_shade_markers": ["C3", "A4"],
  "rules": [
    {
      "id": "dark_shade_force_ai",
      "enabled": false,
      "match": {
        "shade_in": ["C3", "A4"]
      },
      "action": {
        "template_family_override_key": "ai_family"
      }
    }
  ]
}
```

### Routing override rules

```json
{
  "version": 1,
  "enabled": true,
  "template_family_route_overrides": [
    {
      "family_key": "ai",
      "destination_key": "1_9"
    },
    {
      "family_key": "argen",
      "destination_key": "argen"
    }
  ]
}
```

### Argen/contact-model mode settings

```json
{
  "version": 1,
  "enabled": true,
  "modes": {
    "modeless_enabled": false,
    "contact_model_mode": "legacy_default"
  }
}
```

### Template override mappings

```json
{
  "version": 1,
  "enabled": true,
  "overrides": [
    {
      "id": "itero_adz_nonstudy_override",
      "enabled": false,
      "when": {
        "is_itero": true,
        "has_study": false,
        "material_key": "adz"
      },
      "template_key": "ai_adzir"
    }
  ]
}
```

Design notes:
- Use explicit keys (`template_key`, `destination_key`, `family_key`) rather than raw paths.
- Keep matching DSL small and explicit.
- Keep phase-1 schemas constrained and auditable.

---

## 7. Runtime Ownership and Resolution Flow

Target runtime flow once implemented:

1. **Load baseline defaults**
   - Rule modules (`doctor_rules`, `shade_rules`, `routing_rules`, `template_rules`, etc.) expose hardcoded defaults matching current behavior.

2. **Load external business-rule files**
   - New config loader reads `business_rules/v1/*.json` from editable location.
   - Each file parsed independently.

3. **Validate each file**
   - Schema + semantic checks.
   - Invalid file -> reject file, keep defaults for that family.

4. **Build effective rule state**
   - Effective state = defaults + validated overrides.
   - Done per family, not all-or-nothing globally.

5. **Decision modules consume effective state**
   - `template_selector`, `destination_selector`, `manual_review_selector` read centralized rule modules/services.

6. **Resolve route/template keys to existing runtime behavior**
   - Route keys resolve to existing processor path constants.
   - Template keys resolve through existing template path helpers.

7. **Operational settings remain separate**
   - Existing path/credential/UI settings continue through current settings system.
   - Business-rule config does not replace `local_settings`/`admin_settings`.

---

## 8. Validation and Safety Plan

### Validation layers
1. **JSON parse validation**
   - malformed JSON -> file rejected, defaults used.

2. **Schema validation**
   - required keys, type checks, enum checks, allowed action keys.

3. **Semantic validation**
   - duplicate IDs,
   - unknown template keys,
   - unknown destination keys,
   - invalid match clauses.

4. **Conflict handling**
   - deterministic order:
     - explicit file order + rule order.
   - conflicting overrides logged; last-valid-wins only where explicitly allowed.

### Safety/fallback behavior
- Per-file fallback to defaults on failure.
- Never crash import/startup because of business-rule config parse errors.
- Emit clear diagnostic logs and optional admin-visible status summary.
- Keep packaged baseline behavior if rule files are absent.

### User/admin visibility
- Minimal, clear status in existing UI later (e.g., “Business rules loaded with warnings”).
- Detailed diagnostics remain in logs for advanced troubleshooting.

---

## 9. Defaulting and Migration Strategy

### Default derivation
- Phase-1 default values come directly from current centralized rule module constants/logic.

### First-run strategy
- On first run (or first load attempt), optionally create starter `business_rules/v1` files from defaults.
- If creation fails, continue with in-code defaults.

### Packaged deployment strategy
- Package ships with code defaults.
- Editable files live outside package in app data path.
- Deploy tooling can optionally pre-seed starter files per machine/site.

### Existing installs
- No forced migration required:
  - if no business-rule files exist, behavior remains unchanged.
- Optional migration helper can copy starter defaults into editable location.

---

## 10. Integration with Existing Settings/Admin UI

No new dashboard layer required.

### Realistic UI-editable phase-1 candidates
- Doctor override keywords (simple lists/toggles).
- Shade exception markers.
- Route-key overrides for template families.
- Argen mode toggles (simple enum/boolean).

### Better as advanced file edits (initially)
- Template override records with conditional matching.
- Material mapping expansions.
- Complex precedence-sensitive overrides.

### Should stay internal for now
- Scanner heuristics and low-level technical file handling behavior.
- Deep precedence engine internals.

---

## 11. Recommended Phase 1 Implementation Scope

Smallest safe first live scope:

1. **Create files**
   - `business_rules/v1/doctor_overrides.json`
   - `business_rules/v1/shade_overrides.json`
   - `business_rules/v1/routing_overrides.json`

2. **Create loader/validator layer**
   - Load + validate these three files only.
   - Fail-safe fallback per file.

3. **Wire only selected live families**
   - Doctor override keys (limited actions),
   - Shade marker overrides (limited),
   - Route-key overrides (template-family level).

4. **Keep internal/hardcoded for phase 1**
   - template precedence engine,
   - material mapping internals,
   - manual-review internals,
   - naming/suffix internals,
   - scanner heuristics.

---

## 12. Risks and Guardrails

### Risks
- Over-exposing fragile internals too early.
- Confusing destination route keys with filesystem paths.
- Precedence drift from poorly constrained override rules.
- Invalid config causing silent behavior surprises.
- Conflicts between operational settings and business-rule config.

### Guardrails
- Strict key-based schema (no raw paths in business-rule files).
- Narrow phase-1 exposure.
- Explicit rule IDs and deterministic evaluation order.
- Strong validation + per-file fallback to defaults.
- Startup diagnostics and clear warning surfaces.
- Versioned config directory (`v1`) for controlled evolution.

---

## 13. Recommended Execution Plan

### Phase A: Loader + schemas (no behavior change)
- Add business-rule config loader and validators.
- Load files but do not apply overrides yet.
- Validate and log status only.

### Phase B: Doctor/shade/routing live overrides (limited)
- Enable application of validated overrides for phase-1 families only.
- Keep everything else hardcoded.
- Run parity tests where files are absent to confirm baseline unchanged.

### Phase C: Argen mode file + guarded activation
- Add `argen_modes.json` with constrained toggles.
- Enable only the smallest safe mode toggles.

### Phase D: Template override mapping (limited)
- Add bounded template override support with strict key validation.
- Keep precedence ownership and branch engine unchanged.

### Phase E: Later families
- Material mapping exposure, then manual-review exposure, with dedicated safeguards.
- Scanner heuristics only after proven stability and strong operational need.

---

## 14. Suggested First Code Pass After This Plan

Safest first implementation step:

1. Add a read-only business-rule config service:
   - discovers `business_rules/v1/*.json`,
   - parses + validates against narrow schemas,
   - produces an “effective config preview” object.
2. Do **not** apply overrides yet.
3. Log load/validation status.
4. Add tests proving:
   - malformed/missing files do not change runtime behavior,
   - baseline defaults remain authoritative when no valid config exists.

This creates the safety-critical foundation before enabling any live behavior changes.

