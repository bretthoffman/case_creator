@echo off
REM === PRIMARY LAUNCHER (PySide6) ===
REM This is the default launcher for normal daily use.
REM Tkinter fallback launcher: launch_importer_tk_fallback.bat (repo root shim)
set "PROJECT_ROOT=%~dp0..\.."
pushd "%PROJECT_ROOT%"
REM Prefer the Windows launcher; pythonw avoids a console window
where py >nul 2>nul && (
  py -0p >nul 2>nul && (
    REM Try to run with pythonw (no console). This works if Python is properly registered.
    py -w pyside6_ui.py
  ) || (
    REM Fallback to pythonw on PATH
    start "" pythonw pyside6_ui.py
  )
) || (
  REM If 'py' isn't available, fallback to pythonw directly
  start "" pythonw pyside6_ui.py
)
popd
exit /b 0
