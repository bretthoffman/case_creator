# UI Transition Plan (Tkinter -> PySide6 Launcher Default)

## Current UI Entrypoints

### Old Tkinter entrypoints (legacy/fallback)

- Script entrypoint: `import_gui.pyw`
- Legacy launcher path (now fallback): `launch_importer_tk_fallback.bat`

### New PySide6 entrypoints (default)

- Script entrypoint: `pyside6_ui.py`
- Primary launcher path: `launch_importer.bat`

## Recommended Default Launcher Path

Use `launch_importer.bat` as the default for daily use.

Reason:
- It now launches `pyside6_ui.py` directly.
- It preserves the frozen backend boundary and behavior.
- It is the simplest shortcut target for operators.

## Keep Tkinter as Transition Fallback

Tkinter is retained and launchable via:
- `launch_importer_tk_fallback.bat`

This keeps rollback easy without deleting legacy UI code.

## Shortcut/Launcher Targets Going Forward

Recommended desktop/start-menu shortcut target:
- `launch_importer.bat` (primary / PySide6)

Fallback shortcut (optional secondary shortcut for IT/supervisor):
- `launch_importer_tk_fallback.bat` (legacy Tkinter backup)

## Safe Rollback Steps

If PySide6 launcher has issues:

1. Launch via `launch_importer_tk_fallback.bat`.
2. Confirm imports run and outputs remain correct.
3. Temporarily repoint desktop shortcut to fallback launcher if needed.
4. Investigate/fix PySide6 shell issue separately.
5. Restore shortcut to `launch_importer.bat` after verification.

## Notes on Scope/Safety

- This transition only changes launcher/default entry behavior.
- No XML generation logic changed.
- No case processing logic changed.
- No template selection, scan naming, routing, substitution, or ID logic changed.
- Tkinter UI is not deleted in this phase.
