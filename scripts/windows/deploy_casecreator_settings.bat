@echo off
setlocal

REM Optional helper:
REM 1) Ensure %LOCALAPPDATA%\CaseCreator exists
REM 2) Optionally copy admin_settings.json from provided source path
REM
REM Usage:
REM   deploy_casecreator_settings.bat
REM   deploy_casecreator_settings.bat "C:\path\to\admin_settings.json"

set "TARGET_DIR=%LOCALAPPDATA%\CaseCreator"
if not exist "%TARGET_DIR%" (
  mkdir "%TARGET_DIR%"
  if errorlevel 1 (
    echo [ERROR] Failed to create "%TARGET_DIR%"
    exit /b 1
  )
)

if "%~1"=="" (
  echo [OK] Created/verified "%TARGET_DIR%"
  echo [INFO] No admin_settings source path provided. Nothing copied.
  exit /b 0
)

set "SRC_ADMIN=%~1"
if not exist "%SRC_ADMIN%" (
  echo [ERROR] Source file not found: "%SRC_ADMIN%"
  exit /b 1
)

copy /Y "%SRC_ADMIN%" "%TARGET_DIR%\admin_settings.json" >nul
if errorlevel 1 (
  echo [ERROR] Failed to copy admin_settings.json to "%TARGET_DIR%"
  exit /b 1
)

echo [OK] Created/verified "%TARGET_DIR%"
echo [OK] Copied admin_settings.json to "%TARGET_DIR%\admin_settings.json"
exit /b 0
