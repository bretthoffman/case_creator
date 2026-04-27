@echo off
REM === LEGACY FALLBACK LAUNCHER (Tkinter) ===
REM Use only if the primary PySide6 launcher has issues.
set "PROJECT_ROOT=%~dp0..\.."
pushd "%PROJECT_ROOT%"
REM Prefer the Windows launcher; pythonw avoids a console window
where py >nul 2>nul && (
  py -0p >nul 2>nul && (
    REM Try to run with pythonw (no console). This works if Python is properly registered.
    py -w import_gui.pyw
  ) || (
    REM Fallback to pythonw on PATH
    start "" pythonw import_gui.pyw
  )
) || (
  REM If 'py' isn't available, fallback to pythonw directly
  start "" pythonw import_gui.pyw
)
popd
exit /b 0
