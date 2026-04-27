@echo off
setlocal

REM Conservative one-folder PyInstaller build for PySide6 UI only.
REM Includes required runtime data assets:
REM   - templates/
REM   - List of Signature Dr.xlsx
REM   - business_rules_seed/v1/case_creator_rules.yaml (packaged unified seed)

set "PROJECT_DIR=%~dp0..\.."
pushd "%PROJECT_DIR%"

if not exist "pyside6_ui.py" (
  echo [ERROR] Missing entrypoint: pyside6_ui.py
  popd
  exit /b 1
)

if not exist "templates" (
  echo [ERROR] Missing required folder: templates
  popd
  exit /b 1
)

if not exist "List of Signature Dr.xlsx" (
  echo [ERROR] Missing required file: List of Signature Dr.xlsx
  popd
  exit /b 1
)

if not exist "business_rules\v1\case_creator_rules.yaml" (
  echo [ERROR] Missing canonical unified rules file: business_rules\v1\case_creator_rules.yaml
  popd
  exit /b 1
)

REM Refresh packaged seed from canonical unified file (do not edit seed by hand in-repo).
if not exist "business_rules_seed\v1" mkdir "business_rules_seed\v1"
copy /Y "business_rules\v1\case_creator_rules.yaml" "business_rules_seed\v1\case_creator_rules.yaml" >nul
if errorlevel 1 (
  echo [ERROR] Failed to copy canonical unified rules into business_rules_seed\v1\
  popd
  exit /b 1
)

REM Prefer py launcher when available.
where py >nul 2>nul
if %errorlevel%==0 (
  py -m PyInstaller ^
    --noconfirm ^
    --onedir ^
    --windowed ^
    --name "CaseCreator" ^
    --icon "case_creator_icon.ico" ^
    --add-data "templates;templates" ^
    --add-data "List of Signature Dr.xlsx;." ^
    --add-data "business_rules_seed\v1\case_creator_rules.yaml;business_rules_seed\v1" ^
    --hidden-import "openpyxl" ^
    "pyside6_ui.py"
) else (
  python -m PyInstaller ^
    --noconfirm ^
    --onedir ^
    --windowed ^
    --name "CaseCreator" ^
    --icon "case_creator_icon.ico" ^
    --add-data "templates;templates" ^
    --add-data "List of Signature Dr.xlsx;." ^
    --add-data "business_rules_seed\v1\case_creator_rules.yaml;business_rules_seed\v1" ^
    --hidden-import "openpyxl" ^
    "pyside6_ui.py"
)

set "BUILD_EXIT=%errorlevel%"
if not "%BUILD_EXIT%"=="0" (
  echo [ERROR] PyInstaller build failed with exit code %BUILD_EXIT%.
  popd
  exit /b %BUILD_EXIT%
)

echo [OK] Build complete. Check dist\CaseCreator\
popd
exit /b 0
