import html
import json
import os
import subprocess
import sys
import tempfile
import time
from collections import deque
from typing import Dict, List, Tuple

from PySide6.QtCore import QObject, QThread, QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from admin_access import current_user_is_admin
from admin_settings import save_admin_settings_updates
from config import (
    CC_IMPORTED_ROOT,
    EV_INT_BASE,
    EVIDENT_PATH,
    EVO_PASS,
    EVO_USER,
    IMG_PASS,
    IMG_USER,
    TRIOS_SCAN_ROOT,
)
from import_service import build_case_id, get_app_info, import_case_by_id, validate_case_id
from local_settings import save_settings_updates
from local_settings import load_local_settings
from update_check import (
    STATUS_FAILURE,
    STATUS_UP_TO_DATE,
    STATUS_UPDATE_AVAILABLE,
    UpdateCheckResult,
    check_github_latest_release,
)

DEFAULT_YEAR_OPTIONS = ["2022", "2023", "2024", "2025", "2026", "2027"]
DEFAULT_DEFAULT_YEAR = "2026"

THEMES = {
    "Default": {
        "bg": "#2b2b2b",
        "panel": "#1f1f1f",
        "input_bg": "#ffffff",
        "text": "#ffffff",
        "input_text": "#111111",
        "button_bg": "#3d3d3d",
        "button_text": "#ffffff",
        "accent": "#ff1493",
        "log_bg": "#f0f0f0",
        "log_text": "#111111",
        "log_colors": {
            "success": "#1c7c2e",
            "error": "#b00020",
            "warn": "#b36b00",
            "info": "#005bbb",
            "has_study": "#008f39",
            "signature": "#6f42c1",
            "tooth": "#005bbb",
            "shade": "#0b7a75",
            "template": "#a66b00",
            "route": "#d0006f",
            "default": "#111111",
        },
    },
    "Bubble Gum": {
        "bg": "#ffe3f2",
        "panel": "#ffcbe8",
        "input_bg": "#ffffff",
        "text": "#4b2340",
        "input_text": "#35122a",
        "button_bg": "#ff77c6",
        "button_text": "#2a1021",
        "accent": "#ff2fa8",
        "log_bg": "#fff8fc",
        "log_text": "#35122a",
        "log_colors": {
            "success": "#157347", "error": "#b4233c", "warn": "#b26b00", "info": "#0066cc",
            "has_study": "#157347", "signature": "#7a3db8", "tooth": "#0066cc",
            "shade": "#0b7a75", "template": "#a66b00", "route": "#c2185b", "default": "#35122a",
        },
    },
    "Midnight Neon": {
        "bg": "#0f1221", "panel": "#141a2e", "input_bg": "#1d2540", "text": "#e5ecff",
        "input_text": "#e5ecff", "button_bg": "#1f2b52", "button_text": "#e5ecff", "accent": "#00e5ff",
        "log_bg": "#0b1020", "log_text": "#d7e3ff",
        "log_colors": {
            "success": "#00e676", "error": "#ff5252", "warn": "#ffd54f", "info": "#40c4ff",
            "has_study": "#00e676", "signature": "#b388ff", "tooth": "#40c4ff",
            "shade": "#1de9b6", "template": "#ffab40", "route": "#ff4081", "default": "#d7e3ff",
        },
    },
    "Forest Mist": {
        "bg": "#1f2a24", "panel": "#2a3b33", "input_bg": "#f3f7f4", "text": "#e8f3ec",
        "input_text": "#1d2a22", "button_bg": "#3f5f4d", "button_text": "#f3fff8", "accent": "#7cc38a",
        "log_bg": "#edf5ef", "log_text": "#1d2a22",
        "log_colors": {
            "success": "#2e7d32", "error": "#c62828", "warn": "#a66b00", "info": "#1565c0",
            "has_study": "#2e7d32", "signature": "#6a1b9a", "tooth": "#1565c0",
            "shade": "#00796b", "template": "#8d6e00", "route": "#ad1457", "default": "#1d2a22",
        },
    },
    "Solar Flare": {
        "bg": "#2b1a10", "panel": "#3a2416", "input_bg": "#fff7ef", "text": "#ffe8d5",
        "input_text": "#2c180f", "button_bg": "#c84b16", "button_text": "#fff3e0", "accent": "#ff8f00",
        "log_bg": "#fff4e8", "log_text": "#2c180f",
        "log_colors": {
            "success": "#2e7d32", "error": "#b71c1c", "warn": "#ef6c00", "info": "#1565c0",
            "has_study": "#2e7d32", "signature": "#6a1b9a", "tooth": "#1565c0",
            "shade": "#00897b", "template": "#ef6c00", "route": "#d81b60", "default": "#2c180f",
        },
    },
    "Arctic Ice": {
        "bg": "#eaf4fb", "panel": "#d8eaf7", "input_bg": "#ffffff", "text": "#1a3a4a",
        "input_text": "#1a3a4a", "button_bg": "#7ab6d9", "button_text": "#0f2e3d", "accent": "#00a3d9",
        "log_bg": "#ffffff", "log_text": "#1a3a4a",
        "log_colors": {
            "success": "#1b8a5a", "error": "#c62828", "warn": "#9a6b00", "info": "#1565c0",
            "has_study": "#1b8a5a", "signature": "#6a1b9a", "tooth": "#1565c0",
            "shade": "#00796b", "template": "#9a6b00", "route": "#ad1457", "default": "#1a3a4a",
        },
    },
    "Vintage Terminal": {
        "bg": "#101510", "panel": "#171f17", "input_bg": "#0f170f", "text": "#b7f5b7",
        "input_text": "#b7f5b7", "button_bg": "#1f2b1f", "button_text": "#b7f5b7", "accent": "#3ad13a",
        "log_bg": "#0c120c", "log_text": "#b7f5b7",
        "log_colors": {
            "success": "#6cff6c", "error": "#ff7373", "warn": "#ffd166", "info": "#7cc7ff",
            "has_study": "#6cff6c", "signature": "#d0a8ff", "tooth": "#7cc7ff",
            "shade": "#69f0ae", "template": "#ffcc80", "route": "#ff7ab6", "default": "#b7f5b7",
        },
    },
    "Royal Velvet": {
        "bg": "#2a1838", "panel": "#341f46", "input_bg": "#f8f2ff", "text": "#f3e8ff",
        "input_text": "#2a1838", "button_bg": "#6a3ea1", "button_text": "#f8f2ff", "accent": "#b388ff",
        "log_bg": "#fbf7ff", "log_text": "#2a1838",
        "log_colors": {
            "success": "#2e7d32", "error": "#c62828", "warn": "#a66b00", "info": "#1565c0",
            "has_study": "#2e7d32", "signature": "#7b1fa2", "tooth": "#1565c0",
            "shade": "#00796b", "template": "#8d6e00", "route": "#ad1457", "default": "#2a1838",
        },
    },
    "Citrus Pop": {
        "bg": "#fff7d1", "panel": "#ffeaa3", "input_bg": "#ffffff", "text": "#4b3c00",
        "input_text": "#3a2f00", "button_bg": "#ffb300", "button_text": "#3a2f00", "accent": "#ff6f00",
        "log_bg": "#fffdf3", "log_text": "#3a2f00",
        "log_colors": {
            "success": "#2e7d32", "error": "#c62828", "warn": "#b36b00", "info": "#1565c0",
            "has_study": "#2e7d32", "signature": "#6a1b9a", "tooth": "#1565c0",
            "shade": "#00796b", "template": "#b36b00", "route": "#ad1457", "default": "#3a2f00",
        },
    },
    "Ocean Depths": {
        "bg": "#0f2740", "panel": "#143555", "input_bg": "#eef7ff", "text": "#dbefff",
        "input_text": "#0f2740", "button_bg": "#1b5f8a", "button_text": "#eef7ff", "accent": "#00bcd4",
        "log_bg": "#f4fbff", "log_text": "#0f2740",
        "log_colors": {
            "success": "#2e7d32", "error": "#c62828", "warn": "#a66b00", "info": "#0277bd",
            "has_study": "#2e7d32", "signature": "#6a1b9a", "tooth": "#0277bd",
            "shade": "#00695c", "template": "#8d6e00", "route": "#ad1457", "default": "#0f2740",
        },
    },
    "Monochrome Noir": {
        "bg": "#1a1a1a", "panel": "#242424", "input_bg": "#f5f5f5", "text": "#f1f1f1",
        "input_text": "#1a1a1a", "button_bg": "#4a4a4a", "button_text": "#f5f5f5", "accent": "#9e9e9e",
        "log_bg": "#fafafa", "log_text": "#1a1a1a",
        "log_colors": {
            "success": "#2e7d32", "error": "#b71c1c", "warn": "#a66b00", "info": "#1565c0",
            "has_study": "#2e7d32", "signature": "#6a1b9a", "tooth": "#1565c0",
            "shade": "#00796b", "template": "#8d6e00", "route": "#ad1457", "default": "#1a1a1a",
        },
    },
}

LOGOS = {
    "ADS": "A D S",
    "Crown Club": "[ Crown Club ]",
    "Smile": "~ Smile ~",
    "♡ Sugar Baby ♡": "♡ Sugar Baby ♡",
    "Smiley": ":)",
    "Sunglasses": "(⌐■_■)",
    "Star Cats": "✦ /\\_/\\   /\\_/\\ ✦\n  ( o.o ) ( o.o )\n   > ^ <  > ^ <",
    "(╥﹏╥)": "(╥﹏╥)",
    "Coffee": "  ( (\n   ) )\n ........\n |      |]\n \\      /\n  `---'",
    "Shrug": "¯\\_(ツ)_/¯",
}


def get_live_rules_folder_path() -> str:
    local_appdata = os.getenv("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(local_appdata, "CaseCreator", "business_rules", "v1")


def ensure_live_rules_folder_path_exists() -> str:
    folder = get_live_rules_folder_path()
    os.makedirs(folder, exist_ok=True)
    return folder


def get_install_root_path() -> str:
    return os.path.join(os.path.expanduser("~"), "Documents", "CaseCreator")


def get_updater_state_dir() -> str:
    local_appdata = os.getenv("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(local_appdata, "CaseCreator", "update")


def get_updater_log_path() -> str:
    return os.path.join(get_updater_state_dir(), "updater.log")


def append_updater_client_log(message: str) -> None:
    """Best-effort line append from the main app before/around updater launch."""
    try:
        log_path = get_updater_log_path()
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(log_path, "a", encoding="utf-8") as handle:
            handle.write(f"[{ts}] [client] {message}\n")
    except OSError:
        pass


UPDATER_DENTAL_JOKES_QA: Tuple[Tuple[str, str], ...] = (
    (
        "Why did the tooth refuse to apologize?",
        "Because it knew everyone would eventually have to deal with the root issue.",
    ),
    (
        "Why did the molar get kicked out of the group chat?",
        "Too much biting commentary.",
    ),
    (
        "Why did the crown act like royalty?",
        "Because deep down it knew it was covering for something rotten.",
    ),
    (
        "Why did the dentist avoid the haunted house?",
        "Too many cavities with history.",
    ),
    (
        "Why did the wisdom tooth think it was special?",
        "Because it caused chaos and called it growth.",
    ),
    (
        "Why did the floss have trust issues?",
        "It was always getting dragged through someone else's mess.",
    ),
    (
        "Why did the incisor start a fight?",
        "It had a sharp personality and no emotional enamel.",
    ),
    (
        "Why did the denture look suspicious?",
        "It had been in too many mouths to play innocent.",
    ),
    (
        "Why did the toothbrush break up with the toothpaste?",
        "It was tired of carrying the relationship every morning.",
    ),
    (
        "Why did the molar go silent?",
        "It was grinding through something.",
    ),
    (
        "Why did the patient fear the x-ray?",
        "It saw what their smile had been hiding.",
    ),
    (
        "Why did the filling get defensive?",
        "It knew it was just a patch over bad decisions.",
    ),
    (
        "Why did the canine seem unstable?",
        "It was one bad bite away from snapping.",
    ),
    (
        "Why did the retainer feel powerful?",
        "It knew everyone eventually moved back without supervision.",
    ),
    (
        "Why did the plaque act confident?",
        "Because nobody notices the damage until it owns the place.",
    ),
    (
        "Why did the root canal have no friends?",
        "It got too deep too fast.",
    ),
    (
        "Why did the mirror stop judging people?",
        "It had seen enough tongues to lose faith.",
    ),
    (
        "Why did the gumline seem dramatic?",
        "Because once it starts receding, it takes everything personally.",
    ),
    (
        "Why did the extraction seem calm?",
        "Because sometimes removing the problem is the cleanest conversation.",
    ),
    (
        "Why did the bite guard look exhausted?",
        "It spent every night absorbing unspoken rage.",
    ),
    (
        "Why did the veneer seem shallow?",
        "Because that was literally the point.",
    ),
    (
        "Why did the dental chair feel cursed?",
        "Everyone who sat in it suddenly remembered all their sins.",
    ),
    (
        "Why did the scaler enjoy its job?",
        "It liked removing things people pretended weren't there.",
    ),
    (
        "Why did the whitening tray seem arrogant?",
        "Because it made everyone believe brightness was the same as health.",
    ),
    (
        "Why did the drill sound so confident?",
        "It knew fear didn't need lyrics.",
    ),
    (
        "Why did the abscess get attention?",
        "Because ignoring pain is just scheduling drama for later.",
    ),
    (
        "Why did the tooth fairy quit?",
        "She realized she was just buying bones from children.",
    ),
    (
        "Why did the temporary crown feel insecure?",
        "Because even its name admitted nobody planned to keep it.",
    ),
    (
        "Why did the saliva ejector have boundaries?",
        "Because someone had to suck it up.",
    ),
    (
        "Why did the molar hate family gatherings?",
        "Too much pressure from both sides.",
    ),
    (
        "Why did the impression material panic?",
        "It realized it was only valued when it captured someone's flaws.",
    ),
    (
        "Why did the implant act superior?",
        "Because unlike everyone else, it was screwed in on purpose.",
    ),
    (
        "Why did the bridge feel dramatic?",
        "It was literally held together by neighboring problems.",
    ),
    (
        "Why did the tongue get blamed?",
        "Because it was always involved and never took responsibility.",
    ),
    (
        "Why did the cavity feel misunderstood?",
        "It wasn't evil, just enabled.",
    ),
    (
        "Why did the night guard know too much?",
        "It heard what stress does when nobody's watching.",
    ),
    (
        "Why did the dentist like dark humor?",
        "Because decay is basically comedy with consequences.",
    ),
    (
        "Why did the occlusion test get awkward?",
        "It proved some people just don't meet right.",
    ),
    (
        "Why did the bur feel dangerous?",
        "Tiny, fast, and legally allowed near nerves.",
    ),
    (
        "Why did the full arch case scare everyone?",
        "Because sometimes the mouth chooses violence.",
    ),
)


def updater_job_jokes_for_payload() -> List[Dict[str, str]]:
    """Structured jokes for the updater job JSON (PowerShell reads via ConvertFrom-Json)."""
    return [{"q": q, "a": a} for q, a in UPDATER_DENTAL_JOKES_QA]


def _build_updater_powershell_script() -> str:
    return (
        r"""
param(
  [Parameter(Mandatory = $true)]
  [string]$JobPath
)

$logDir = Join-Path $env:LOCALAPPDATA "CaseCreator\update"
$logFile = Join-Path $logDir "updater.log"

function Write-UpdaterLog([string]$line) {
  try {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff"
    Add-Content -LiteralPath $logFile -Value ("[$ts] [updater] " + $line) -Encoding UTF8
  } catch { }
}

Write-UpdaterLog "IMMEDIATE: Case Creator updater script entry (first line after param)"
try {
  [Console]::WriteLine("[Case Creator Updater] Started. Log: $logFile")
} catch {
  Write-Host "[Case Creator Updater] Started. Log: $logFile"
}

if ([string]::IsNullOrWhiteSpace($JobPath)) {
  Write-UpdaterLog "FATAL: -JobPath parameter is empty"
  Write-Host "ERROR: Missing update job path (-JobPath). Launcher or invocation may be wrong." -ForegroundColor Red
  exit 2
}
if (-not (Test-Path -LiteralPath $JobPath)) {
  Write-UpdaterLog ("FATAL: Job file not found at: " + $JobPath)
  Write-Host ("ERROR: Update job file not found:`n" + $JobPath) -ForegroundColor Red
  exit 2
}

$job = $null
try {
  $jobRaw = Get-Content -LiteralPath $JobPath -Raw -ErrorAction Stop
  $job = $jobRaw | ConvertFrom-Json
} catch {
  Write-UpdaterLog ("FATAL: Could not parse job JSON: " + $_.Exception.Message)
  Write-Host ("ERROR: Invalid or unreadable job JSON.`n" + $_.Exception.Message) -ForegroundColor Red
  exit 3
}

if ($null -eq $job.jokes) {
  Write-UpdaterLog "FATAL: Job JSON missing jokes array"
  Write-Host "ERROR: Update job is missing jokes data (expected jokes from client)." -ForegroundColor Red
  exit 4
}
$jokeProbe = @($job.jokes)
if ($jokeProbe.Length -lt 1) {
  Write-UpdaterLog "FATAL: Job jokes array is empty"
  Write-Host "ERROR: Update job jokes list is empty." -ForegroundColor Red
  exit 4
}

$ProgressPreference = "SilentlyContinue"
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Windows.Forms | Out-Null
try { Add-Type -AssemblyName System.Net.Http } catch { }

$script:JokeSync = $null
$script:JokeState = $null

function Write-Step([string]$line) {
  Write-Host $line
  Write-UpdaterLog $line
}

function Show-Message([string]$msg) {
  try {
    [System.Windows.Forms.MessageBox]::Show($msg, "Case Creator Updater") | Out-Null
  } catch { }
}

function Stop-JokeStream([hashtable]$state) {
  if ($null -eq $state -or $null -eq $state.PS) { return }
  try { $null = $state.PS.EndInvoke($state.Handle) } catch { }
  try { $state.PS.Dispose() } catch { }
  try {
    if ($null -ne $state.PS.Runspace) {
      $state.PS.Runspace.Close()
      $state.PS.Runspace.Dispose()
    }
  } catch { }
}

function Start-JokeRunspace {
  param([hashtable]$sync, [object[]]$deck)
  $rs = [runspacefactory]::CreateRunspace()
  $rs.Open()
  $ps = [powershell]::Create()
  $ps.Runspace = $rs
  [void]$ps.AddScript({
    param($syncRef, $jokeDeckInner)
    function Write-TypewriterToConsole([string]$line, [int]$maxMs) {
      if ($null -eq $line -or $line.Length -lt 1) { [Console]::WriteLine(); return }
      $n = $line.Length
      $per = [int]($maxMs / $n)
      if ($per -lt 1) { $per = 1 }
      elseif ($per -gt 30) { $per = 30 }
      for ($ti = 0; $ti -lt $n; $ti++) {
        if ($syncRef.Stop) { break }
        [Console]::Write($line.Substring($ti, 1))
        Start-Sleep -Milliseconds $per
      }
      [Console]::WriteLine()
    }
    Start-Sleep -Milliseconds ((Get-Random -Minimum 2000 -Maximum 3001))
    if ($syncRef.Stop) { return }
    Write-TypewriterToConsole "While you wait, how about some jokes?" 900
    for ($ji = 0; $ji -lt $jokeDeckInner.Length; $ji++) {
      if ($syncRef.Stop) { break }
      $pair = $jokeDeckInner[$ji]
      Start-Sleep -Milliseconds ((Get-Random -Minimum 2000 -Maximum 3001))
      if ($syncRef.Stop) { break }
      Write-TypewriterToConsole ("Q: " + $pair.Q) 900
      Start-Sleep -Milliseconds ((Get-Random -Minimum 2000 -Maximum 3001))
      if ($syncRef.Stop) { break }
      Write-TypewriterToConsole ("A: " + $pair.A) 900
    }
  }).AddArgument($sync).AddArgument($deck)
  $handle = $ps.BeginInvoke()
  return @{ PS = $ps; Handle = $handle }
}

function Stop-JokesIfRunning {
  try {
    if ($null -ne $script:JokeSync) { $script:JokeSync.Stop = $true }
  } catch { }
  Stop-JokeStream $script:JokeState
  $script:JokeState = $null
}

function Save-UpdateZipWithMbProgress {
  param([string]$Uri, [string]$OutPath)
  function Emit-MbProgress([long]$BytesSoFar, [bool]$HasTotal, [long]$TotalBytes) {
    $mb = [math]::Round([double]$BytesSoFar / 1MB, 1)
    if ($HasTotal) {
      $totalMb = [math]::Round([double]$TotalBytes / 1MB, 1)
      Write-Host ("Downloading update... " + $mb + " MB / " + $totalMb + " MB")
    } else {
      Write-Host ("Downloading update... " + $mb + " MB")
    }
  }
  $handler = New-Object System.Net.Http.HttpClientHandler
  $handler.AllowAutoRedirect = $true
  $client = New-Object System.Net.Http.HttpClient($handler)
  $client.Timeout = [timespan]::FromHours(2)
  try {
    $resp = $client.GetAsync($Uri).Result
    if (-not $resp.IsSuccessStatusCode) {
      throw ("HTTP " + [int]$resp.StatusCode + " " + $resp.ReasonPhrase)
    }
    $hasTotal = $false
    $totalBytes = [long]0
    try {
      $lenObj = $resp.Content.Headers.ContentLength
      if ($null -ne $lenObj) {
        $lv = $lenObj
        if (($lenObj | Get-Member -Name HasValue -ErrorAction SilentlyContinue) -and $lenObj.HasValue) {
          $lv = $lenObj.Value
        }
        if ($null -ne $lv -and [long]$lv -gt 0) {
          $hasTotal = $true
          $totalBytes = [long]$lv
        }
      }
    } catch { }
    $inStream = $resp.Content.ReadAsStreamAsync().Result
    $outFs = [System.IO.File]::Create($OutPath)
    try {
      $buf = New-Object byte[] 65536
      $got = [long]0
      Emit-MbProgress -BytesSoFar $got -HasTotal $hasTotal -TotalBytes $totalBytes
      $lastLog = [Environment]::TickCount
      while ($true) {
        $nr = $inStream.Read($buf, 0, $buf.Length)
        if ($nr -le 0) { break }
        $outFs.Write($buf, 0, $nr)
        $got = $got + [long]$nr
        $tickNow = [Environment]::TickCount
        $elapsed = $tickNow - $lastLog
        if ($elapsed -lt 0) { $elapsed = 400 }
        if ($elapsed -ge 400) {
          Emit-MbProgress -BytesSoFar $got -HasTotal $hasTotal -TotalBytes $totalBytes
          $lastLog = $tickNow
        }
      }
      Emit-MbProgress -BytesSoFar $got -HasTotal $hasTotal -TotalBytes $totalBytes
    } finally {
      $outFs.Close()
    }
  } finally {
    $client.Dispose()
    $handler.Dispose()
  }
  Write-Host "Download complete."
}

function Fail-And-Exit([string]$msg) {
  Stop-JokesIfRunning
  Write-UpdaterLog ("FATAL: " + $msg)
  Write-Host ("ERROR: " + $msg) -ForegroundColor Red
  Show-Message $msg
  Write-UpdaterLog "FINAL: failure"
  exit 1
}

function Move-Item-WithRetry {
  param(
    [Parameter(Mandatory = $true)]
    [string]$LiteralPath,
    [Parameter(Mandatory = $true)]
    [string]$Destination,
    [int]$MaxAttempts = 12,
    [int]$DelayMilliseconds = 800,
    [string]$StepLabel = "move"
  )
  for ($a = 1; $a -le $MaxAttempts; $a++) {
    try {
      Write-UpdaterLog ("[" + $StepLabel + "] attempt " + $a + "/" + $MaxAttempts + " `"$LiteralPath`" -> `"$Destination`" (cwd=" + (Get-Location).Path + ")")
      Move-Item -LiteralPath $LiteralPath -Destination $Destination -ErrorAction Stop
      Write-UpdaterLog ("[" + $StepLabel + "] success on attempt " + $a)
      return
    } catch {
      Write-UpdaterLog ("[" + $StepLabel + "] attempt " + $a + " failed: " + $_.Exception.Message)
      if ($a -ge $MaxAttempts) {
        throw $_
      }
      Start-Sleep -Milliseconds $DelayMilliseconds
    }
  }
}

Write-UpdaterLog "===== Updater launch start ====="
Write-Step "Case Creator updater starting (log file: $logFile)"

$initialCwd = (Get-Location).Path
Write-UpdaterLog ("Initial PowerShell working directory: " + $initialCwd)
$scriptFullPath = $PSCommandPath
if ([string]::IsNullOrWhiteSpace($scriptFullPath)) {
  $scriptFullPath = "(unknown)"
}
Write-UpdaterLog ("Updater script path: " + $scriptFullPath)
$runnerRoot = Split-Path -Parent $scriptFullPath
if ([string]::IsNullOrWhiteSpace($runnerRoot)) {
  $runnerRoot = $env:TEMP
}
Set-Location -LiteralPath $runnerRoot
Write-UpdaterLog ("Working directory set to: " + (Get-Location).Path)

Write-UpdaterLog ("Job file path: " + $JobPath)

$pidToWait = [int]$job.current_pid
Write-UpdaterLog ("Waiting for main app PID " + $pidToWait + " to exit (poll up to ~45s)")

$pidGone = $false
for ($i = 0; $i -lt 90; $i++) {
  $mainProc = Get-Process -Id $pidToWait -ErrorAction SilentlyContinue
  if (-not $mainProc) {
    $pidGone = $true
    Write-UpdaterLog ("Main app PID " + $pidToWait + " no longer running (poll " + ($i + 1) + "/90)")
    break
  }
  Start-Sleep -Milliseconds 500
}
if (-not $pidGone) {
  Write-UpdaterLog "WARNING: main app PID still running after full wait window (~45s); folder move may fail"
}
Write-UpdaterLog "Post-exit stabilization delay (2s) before touching install folder"
Start-Sleep -Seconds 2

$tempRoot = Join-Path $env:TEMP ("CaseCreatorUpdaterRun-" + [DateTimeOffset]::Now.ToUnixTimeMilliseconds())
$downloadDir = Join-Path $tempRoot "download"
$extractDir = Join-Path $tempRoot "extract"
New-Item -ItemType Directory -Path $downloadDir -Force | Out-Null
New-Item -ItemType Directory -Path $extractDir -Force | Out-Null
Write-UpdaterLog ("Temp workspace: " + $tempRoot)

$zipName = [string]$job.zip_asset_name
if ([string]::IsNullOrWhiteSpace($zipName)) {
  $zipName = "CaseCreator-win64.zip"
}
$zipPath = Join-Path $downloadDir $zipName

$deckForJokes = @($job.jokes)
for ($si = $deckForJokes.Length - 1; $si -gt 0; $si--) {
  $sj = Get-Random -Minimum 0 -Maximum ($si + 1)
  $t = $deckForJokes[$si]
  $deckForJokes[$si] = $deckForJokes[$sj]
  $deckForJokes[$sj] = $t
}
$script:JokeSync = [hashtable]::Synchronized(@{ Stop = $false })
$script:JokeState = Start-JokeRunspace -sync $script:JokeSync -deck $deckForJokes

Write-UpdaterLog ("Download start: " + [string]$job.zip_asset_url)
try {
  Save-UpdateZipWithMbProgress -Uri ([string]$job.zip_asset_url) -OutPath $zipPath
  Write-UpdaterLog ("Download success: " + $zipPath)
} catch {
  Write-UpdaterLog ("Download failure: " + $_.Exception.Message)
  Fail-And-Exit ("Failed to download update zip.`n" + $_.Exception.Message)
}

$checksumUrl = [string]$job.checksum_asset_url
if (-not [string]::IsNullOrWhiteSpace($checksumUrl)) {
  Write-UpdaterLog "Checksum verification start (remote .sha256 present)"
  $checksumPath = Join-Path $downloadDir ($zipName + ".sha256")
  try {
    Invoke-WebRequest -Uri $checksumUrl -OutFile $checksumPath -UseBasicParsing
    $checksumRaw = (Get-Content -LiteralPath $checksumPath -Raw).Trim()
    $expected = ($checksumRaw -split '\s+')[0].ToLower()
    $actual = (Get-FileHash -Path $zipPath -Algorithm SHA256).Hash.ToLower()
    if ($expected -ne $actual) {
      Write-UpdaterLog ("Checksum mismatch: expected=" + $expected + " actual=" + $actual)
      Fail-And-Exit "Checksum verification failed for downloaded update package."
    }
    Write-UpdaterLog "Checksum verification OK"
  } catch {
    Write-UpdaterLog ("Checksum verification failure: " + $_.Exception.Message)
    Fail-And-Exit ("Failed checksum verification.`n" + $_.Exception.Message)
  }
} else {
  Write-UpdaterLog "Checksum verification skipped (no checksum_asset_url in job)"
}

Write-UpdaterLog ("Extract start -> " + $extractDir)
try {
  Expand-Archive -Path $zipPath -DestinationPath $extractDir -Force
  Write-UpdaterLog "Extract success"
} catch {
  Write-UpdaterLog ("Extract failure: " + $_.Exception.Message)
  Fail-And-Exit ("Failed to extract update zip.`n" + $_.Exception.Message)
}

$newRoot = Join-Path $extractDir "CaseCreator"
$newExe = Join-Path $newRoot "CaseCreator.exe"
$newInternal = Join-Path $newRoot "_internal"
$structOk = $true
if (-not (Test-Path -LiteralPath $newExe)) {
  Write-UpdaterLog "Extracted structure validation FAIL: missing CaseCreator.exe"
  $structOk = $false
}
if (-not (Test-Path -LiteralPath $newInternal)) {
  Write-UpdaterLog "Extracted structure validation FAIL: missing _internal folder"
  $structOk = $false
}
if (-not $structOk) {
  Fail-And-Exit "Extracted package missing required files (CaseCreator.exe or _internal)."
}
Write-UpdaterLog "Extracted structure validation OK"

$installRoot = [string]$job.install_root
$backupRoot = $installRoot + ".backup-" + (Get-Date -Format "yyyyMMdd-HHmmss")
Write-UpdaterLog ("Install root: " + $installRoot)
Write-UpdaterLog ("Backup path (if replace proceeds): " + $backupRoot)

if (Test-Path -LiteralPath $installRoot) {
  try {
    Write-UpdaterLog ("Moving existing install to backup: " + $backupRoot)
    Move-Item-WithRetry -LiteralPath $installRoot -Destination $backupRoot -StepLabel "backup-move"
    Write-UpdaterLog "Backup move success"
  } catch {
    Write-UpdaterLog ("Backup move failure after retries: " + $_.Exception.Message)
    $lockHint = ""
    if ($_.Exception.Message -match 'in use|being used|cannot access') {
      $lockHint = "`n`nThe install folder may still be locked (Explorer, antivirus, or another program). Close windows under that folder, wait a few seconds, and try again."
    }
    Fail-And-Exit ("Failed to move existing install to backup.`n" + $_.Exception.Message + $lockHint)
  }
} else {
  Write-UpdaterLog "No existing install folder; fresh install path"
}

try {
  Write-UpdaterLog ("Moving extracted app into install root: " + $installRoot)
  Move-Item-WithRetry -LiteralPath $newRoot -Destination $installRoot -StepLabel "install-move"
  Write-UpdaterLog "Install folder replacement success"
} catch {
  Write-UpdaterLog ("Install folder replacement failure: " + $_.Exception.Message)
  if ((Test-Path -LiteralPath $backupRoot) -and (-not (Test-Path -LiteralPath $installRoot))) {
    Write-UpdaterLog "Rollback: restoring backup to install root"
    try {
      Move-Item -LiteralPath $backupRoot -Destination $installRoot
      Write-UpdaterLog "Rollback success (install restored from backup)"
    } catch {
      Write-UpdaterLog ("Rollback failed: " + $_.Exception.Message)
    }
  } else {
    Write-UpdaterLog "Rollback not attempted (backup or install state unexpected)"
  }
  Fail-And-Exit ("Failed to replace install folder.`n" + $_.Exception.Message)
}

$launchExe = Join-Path $installRoot "CaseCreator.exe"
if (-not (Test-Path -LiteralPath $launchExe)) {
  Write-UpdaterLog "Post-replace validation FAIL: CaseCreator.exe missing"
  if ((Test-Path -LiteralPath $backupRoot) -and (-not (Test-Path -LiteralPath $installRoot))) {
    Write-UpdaterLog "Rollback: restoring backup after missing exe"
    try {
      Move-Item -LiteralPath $backupRoot -Destination $installRoot
      Write-UpdaterLog "Rollback success after missing exe"
    } catch {
      Write-UpdaterLog ("Rollback failed: " + $_.Exception.Message)
    }
  }
  Fail-And-Exit "Updated install is missing CaseCreator.exe after replacement."
}

Write-UpdaterLog ("Relaunch attempt: " + $launchExe)
try {
  Start-Process -FilePath $launchExe | Out-Null
  Write-UpdaterLog "Relaunch Start-Process succeeded"
} catch {
  Write-UpdaterLog ("Relaunch failure: " + $_.Exception.Message)
  if ((Test-Path -LiteralPath $backupRoot) -and (Test-Path -LiteralPath $installRoot)) {
    Write-UpdaterLog "Rollback: removing failed install and restoring backup"
    try {
      Remove-Item -LiteralPath $installRoot -Recurse -Force
      Move-Item -LiteralPath $backupRoot -Destination $installRoot
      Write-UpdaterLog "Rollback success after relaunch failure"
    } catch {
      Write-UpdaterLog ("Rollback failed: " + $_.Exception.Message)
    }
  }
  Fail-And-Exit ("Update installed but failed to relaunch Case Creator.`n" + $_.Exception.Message)
}

Stop-JokesIfRunning
Write-UpdaterLog "FINAL: success"
Write-Step "Update finished successfully. Log: $logFile"
Show-Message "Update installed successfully. Relaunching Case Creator."
Start-Sleep -Seconds 2
exit 0
"""
    )


def _write_updater_cmd_launcher(runner_dir: str) -> str:
    """
    Windows CMD wrapper: keeps the console open (pause) when PowerShell exits non-zero
    so parse errors and early failures are readable.
    """
    path = os.path.join(runner_dir, "case_creator_updater.cmd")
    # ASCII + CRLF: reliable for cmd.exe
    content = (
        '@echo off\r\n'
        'setlocal\r\n'
        'cd /d "%~dp0"\r\n'
        'powershell.exe -NoProfile -NoLogo -ExecutionPolicy Bypass '
        '-File "%~dp0case_creator_updater.ps1" -JobPath "%~1"\r\n'
        'if errorlevel 1 (\r\n'
        '  echo.\r\n'
        '  echo Case Creator updater exited with an error. Review messages above.\r\n'
        '  echo Log file: %LOCALAPPDATA%\\CaseCreator\\update\\updater.log\r\n'
        '  pause\r\n'
        ')\r\n'
        'endlocal\r\n'
    )
    with open(path, "w", encoding="ascii", newline="\n") as handle:
        handle.write(content)
    return path


def launch_external_updater(result: UpdateCheckResult, current_version: str) -> subprocess.Popen:
    if os.name != "nt":
        raise RuntimeError("Updater is currently supported on Windows only.")
    if not result.zip_asset_url:
        raise RuntimeError("Release package URL not found in latest release assets.")

    runner_dir = os.path.join(tempfile.gettempdir(), "CaseCreatorUpdater")
    os.makedirs(runner_dir, exist_ok=True)
    timestamp = str(int(time.time() * 1000))
    job_path = os.path.join(runner_dir, f"update-job-{timestamp}.json")
    script_path = os.path.join(runner_dir, "case_creator_updater.ps1")

    install_root = get_install_root_path()
    intended_release = result.latest_tag or result.latest_version or ""
    payload = {
        "current_version": current_version,
        "latest_tag": result.latest_tag or "",
        "zip_asset_name": result.zip_asset_name or "",
        "zip_asset_url": result.zip_asset_url,
        "checksum_asset_url": result.checksum_asset_url or "",
        "install_root": install_root,
        "current_pid": os.getpid(),
        "jokes": updater_job_jokes_for_payload(),
    }
    with open(job_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=True)
        f.write("\n")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(_build_updater_powershell_script())

    launcher_path = _write_updater_cmd_launcher(runner_dir)
    comspec = os.environ.get("COMSPEC", "cmd.exe")
    popen_argv = [comspec, "/c", launcher_path, job_path]
    append_updater_client_log(
        "Launching external updater | "
        f"launcher={launcher_path} | script={script_path} | job={job_path} | "
        f"subprocess_cwd={runner_dir} | comspec={comspec} | "
        f"install_root={install_root} | "
        f"intended_release={intended_release!r} | current_version={current_version!r} | "
        f"pid={os.getpid()}"
    )
    append_updater_client_log("subprocess argv (JSON): " + json.dumps(popen_argv))

    creationflags = 0
    if os.name == "nt":
        # Visible console window so operators can see progress during this debugging phase.
        creationflags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)

    try:
        proc = subprocess.Popen(
            popen_argv,
            creationflags=creationflags,
            close_fds=True,
            cwd=runner_dir,
        )
    except OSError as exc:
        append_updater_client_log(f"ERROR: subprocess.Popen failed: {exc!r}")
        raise

    append_updater_client_log(f"Updater process started (child pid={proc.pid})")
    return proc


class SettingsDialog(QDialog):
    def __init__(
        self,
        theme_name,
        logo_name,
        display_title,
        display_subtitle,
        year_options,
        default_year,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(760, 520)
        self._theme_name = theme_name
        self._logo_name = logo_name
        self._display_title = display_title
        self._display_subtitle = display_subtitle
        self._year_options = list(year_options)
        self._default_year = default_year
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        grid = QGridLayout()
        layout.addLayout(grid)

        self.evident_input = QLineEdit(EVIDENT_PATH)
        self.trios_input = QLineEdit(TRIOS_SCAN_ROOT)
        self.cc_imported_input = QLineEdit(CC_IMPORTED_ROOT)

        self._add_path_row(grid, 0, "Evident Path", self.evident_input)
        self._add_path_row(grid, 1, "Trios Scan Root", self.trios_input)
        self._add_path_row(grid, 2, "Imported Cases Root", self.cc_imported_input)

        ui_grid = QGridLayout()
        layout.addLayout(ui_grid)

        ui_grid.addWidget(QLabel("Theme"), 0, 0)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()))
        self.theme_combo.setCurrentText(self._theme_name if self._theme_name in THEMES else "Default")
        ui_grid.addWidget(self.theme_combo, 0, 1)

        ui_grid.addWidget(QLabel("Logo"), 1, 0)
        self.logo_combo = QComboBox()
        self.logo_combo.addItems(list(LOGOS.keys()))
        self.logo_combo.setCurrentText(self._logo_name if self._logo_name in LOGOS else "ADS")
        ui_grid.addWidget(self.logo_combo, 1, 1)

        ui_grid.addWidget(QLabel("Display Title"), 2, 0)
        self.display_title_input = QLineEdit(self._display_title)
        ui_grid.addWidget(self.display_title_input, 2, 1)

        ui_grid.addWidget(QLabel("Display Subtitle"), 3, 0)
        self.display_subtitle_input = QLineEdit(self._display_subtitle)
        ui_grid.addWidget(self.display_subtitle_input, 3, 1)

        years_grid = QGridLayout()
        layout.addLayout(years_grid)
        years_grid.addWidget(QLabel("Year Options"), 0, 0)
        self.year_list = QListWidget()
        for year in self._year_options:
            self.year_list.addItem(year)
        years_grid.addWidget(self.year_list, 1, 0, 3, 1)

        self.add_year_button = QPushButton("Add Year")
        self.add_year_button.clicked.connect(self._add_year)
        years_grid.addWidget(self.add_year_button, 1, 1)

        self.remove_year_button = QPushButton("Remove Selected")
        self.remove_year_button.clicked.connect(self._remove_selected_year)
        years_grid.addWidget(self.remove_year_button, 2, 1)

        years_grid.addWidget(QLabel("Default Year"), 3, 1)
        self.default_year_combo = QComboBox()
        years_grid.addWidget(self.default_year_combo, 4, 1)
        self._sync_default_year_combo()

        self.open_rules_folder_button = QPushButton("Open Rules Folder")
        self.open_rules_folder_button.clicked.connect(self._open_rules_folder)
        layout.addWidget(self.open_rules_folder_button, alignment=Qt.AlignmentFlag.AlignLeft)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _add_path_row(self, grid, row, label_text, line_edit):
        label = QLabel(label_text)
        browse = QPushButton("Browse")
        browse.clicked.connect(lambda: self._browse_folder(line_edit))

        grid.addWidget(label, row, 0)
        grid.addWidget(line_edit, row, 1)
        grid.addWidget(browse, row, 2)

    def _browse_folder(self, target_input):
        chosen = QFileDialog.getExistingDirectory(self, "Select Folder", target_input.text().strip())
        if chosen:
            target_input.setText(chosen)

    def settings_payload(self):
        year_options = self._collect_year_options()
        if not year_options:
            year_options = list(DEFAULT_YEAR_OPTIONS)
        default_year = self.default_year_combo.currentText().strip()
        if default_year not in year_options:
            default_year = year_options[0]

        return {
            "EVIDENT_PATH": self.evident_input.text().strip(),
            "TRIOS_SCAN_ROOT": self.trios_input.text().strip(),
            "CC_IMPORTED_ROOT": self.cc_imported_input.text().strip(),
            "UI_THEME": self.theme_combo.currentText(),
            "UI_LOGO": self.logo_combo.currentText(),
            "UI_DISPLAY_TITLE": self.display_title_input.text().strip(),
            "UI_DISPLAY_SUBTITLE": self.display_subtitle_input.text().strip(),
            "UI_YEAR_OPTIONS": year_options,
            "UI_DEFAULT_YEAR": default_year,
        }

    def _collect_year_options(self):
        return [self.year_list.item(i).text().strip() for i in range(self.year_list.count()) if self.year_list.item(i).text().strip()]

    def _sync_default_year_combo(self):
        years = self._collect_year_options()
        if not years:
            years = list(DEFAULT_YEAR_OPTIONS)
            self.year_list.clear()
            for year in years:
                self.year_list.addItem(year)
        self.default_year_combo.clear()
        self.default_year_combo.addItems(years)
        if self._default_year in years:
            self.default_year_combo.setCurrentText(self._default_year)
        else:
            self.default_year_combo.setCurrentText(years[0])

    def _add_year(self):
        value, ok = QInputDialog.getText(self, "Add Year", "Year (e.g. 2028):")
        if not ok:
            return
        year = value.strip()
        if not year:
            return
        if not (len(year) == 4 and year.isdigit()):
            QMessageBox.warning(self, "Invalid Year", "Year must be a 4-digit number.")
            return
        existing = self._collect_year_options()
        if year in existing:
            return
        self.year_list.addItem(year)
        self._default_year = self.default_year_combo.currentText().strip() or self._default_year
        self._sync_default_year_combo()

    def _remove_selected_year(self):
        row = self.year_list.currentRow()
        if row < 0:
            return
        self.year_list.takeItem(row)
        self._default_year = self.default_year_combo.currentText().strip() or self._default_year
        self._sync_default_year_combo()

    def _open_rules_folder(self):
        try:
            folder = ensure_live_rules_folder_path_exists()
            if os.name == "nt":
                os.startfile(folder)  # type: ignore[attr-defined]
            else:
                QMessageBox.information(self, "Rules Folder", f"Rules folder:\n{folder}")
        except Exception as exc:
            QMessageBox.warning(self, "Rules Folder", f"Cannot open rules folder.\n{exc}")


class ImportWorker(QObject):
    log = Signal(str)
    error = Signal(str)
    finished = Signal()

    def __init__(self, case_id):
        super().__init__()
        self.case_id = case_id

    def run(self):
        def emit_log(message):
            self.log.emit(str(message))

        try:
            result = import_case_by_id(self.case_id, emit_log)
            if result is not None:
                self.log.emit(str(result))
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            self.finished.emit()


class UpdateCheckWorker(QObject):
    finished = Signal(object)

    def __init__(self, current_version: str):
        super().__init__()
        self.current_version = current_version

    def run(self):
        result = check_github_latest_release(current_version=self.current_version)
        self.finished.emit(result)


class UpdateCheckDialog(QDialog):
    def __init__(self, current_version: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Check for Update")
        self.resize(420, 170)
        self._thread = None
        self._worker = None
        self._result = None
        self._current_version = current_version
        self._setup_ui(current_version)
        self._start_check(current_version)

    def _setup_ui(self, current_version: str):
        layout = QVBoxLayout(self)
        self.current_label = QLabel(f"Current version: v{current_version}")
        self.status_label = QLabel("Checking for updates...")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.current_label)
        layout.addWidget(self.status_label)
        buttons_row = QHBoxLayout()
        self.update_now_button = QPushButton("Update Now")
        self.update_now_button.setEnabled(False)
        self.update_now_button.clicked.connect(self._on_update_now_clicked)
        buttons_row.addWidget(self.update_now_button)
        buttons_row.addStretch(1)
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        buttons_row.addWidget(self.close_button)
        layout.addLayout(buttons_row)

    def _start_check(self, current_version: str):
        self._worker = UpdateCheckWorker(current_version)
        self._thread = QThread(self)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_check_finished)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._clear_thread_refs)
        self._thread.start()

    def _on_check_finished(self, result: UpdateCheckResult):
        self._result = result
        if result.status == STATUS_UP_TO_DATE:
            self.status_label.setText("You're up to date.")
            self.update_now_button.setEnabled(False)
        elif result.status == STATUS_UPDATE_AVAILABLE:
            latest = result.latest_tag or result.latest_version or "(unknown)"
            if result.zip_asset_url:
                self.status_label.setText(f"Update available: {latest}\nInstall now?")
                self.update_now_button.setEnabled(True)
            else:
                self.status_label.setText(
                    f"Update available: {latest}\nRelease package asset not found."
                )
                self.update_now_button.setEnabled(False)
        elif result.status == STATUS_FAILURE:
            self.status_label.setText("Could not check for updates.")
            self.update_now_button.setEnabled(False)
        else:
            self.status_label.setText("Could not check for updates.")
            self.update_now_button.setEnabled(False)

    def _on_update_now_clicked(self):
        if self._result is None or self._result.status != STATUS_UPDATE_AVAILABLE:
            return
        confirmation = QMessageBox.question(
            self,
            "Update Available",
            "Update now?\nThe app will close while the updater installs the new version.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return
        try:
            proc = launch_external_updater(self._result, self._current_version)
        except Exception as exc:
            append_updater_client_log(f"ERROR: launch_external_updater raised: {exc!r}")
            QMessageBox.warning(self, "Updater Error", f"Could not start updater.\n{exc}")
            return

        time.sleep(0.85)
        early = proc.poll()
        if early is not None:
            log_path = get_updater_log_path()
            append_updater_client_log(
                f"ERROR: updater PowerShell exited immediately with code {early}"
            )
            QMessageBox.warning(
                self,
                "Updater Error",
                "The updater process exited immediately (often a script error or blocked PowerShell).\n\n"
                f"Exit code: {early}\nLog file:\n{log_path}",
            )
            return

        append_updater_client_log(
            "Updater launch confirmed; scheduling app shutdown in 1500ms"
        )
        app = QApplication.instance()
        self.accept()
        if app is not None:
            QTimer.singleShot(1500, app.quit)

    def _clear_thread_refs(self):
        self._thread = None
        self._worker = None


class AdvancedSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Advanced Settings")
        self.resize(760, 240)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        grid = QGridLayout()
        layout.addLayout(grid)

        self.ev_int_base_input = QLineEdit(EV_INT_BASE)
        self.evo_user_input = QLineEdit(EVO_USER)
        self.evo_pass_input = QLineEdit(EVO_PASS)
        self.img_user_input = QLineEdit(IMG_USER)
        self.img_pass_input = QLineEdit(IMG_PASS)

        self.evo_pass_input.setEchoMode(QLineEdit.Password)
        self.img_pass_input.setEchoMode(QLineEdit.Password)

        self._add_row(grid, 0, "Evolution API Base URL", self.ev_int_base_input)
        self._add_row(grid, 1, "Evolution Username", self.evo_user_input)
        self._add_row(grid, 2, "Evolution Password", self.evo_pass_input)
        self._add_row(grid, 3, "Image Server Username", self.img_user_input)
        self._add_row(grid, 4, "Image Server Password", self.img_pass_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _add_row(self, grid, row, label_text, line_edit):
        label = QLabel(label_text)
        grid.addWidget(label, row, 0)
        grid.addWidget(line_edit, row, 1)

    def settings_payload(self):
        return {
            "EV_INT_BASE": self.ev_int_base_input.text().strip(),
            "EVO_USER": self.evo_user_input.text().strip(),
            "EVO_PASS": self.evo_pass_input.text().strip(),
            "IMG_USER": self.img_user_input.text().strip(),
            "IMG_PASS": self.img_pass_input.text().strip(),
        }


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._case_queue = deque()
        self._active_case_id = None
        self._thread = None
        self._worker = None
        self._timeout_timer = None
        self._load_ui_preferences()
        self._setup_ui()

    def _load_ui_preferences(self):
        app_info = get_app_info()
        settings = load_local_settings()

        theme_name = settings.get("UI_THEME", "Default")
        self._theme_name = theme_name if theme_name in THEMES else "Default"
        logo_name = settings.get("UI_LOGO", "ADS")
        self._logo_name = logo_name if logo_name in LOGOS else "ADS"

        mode = str(settings.get("UI_COLOR_MODE", "color")).strip().lower()
        self._color_mode = mode != "standard"

        title_default = app_info.get("app_name", "3Shape Case Importer")
        subtitle_default = f"v{app_info.get('app_version', '0.0.0')}"
        self._display_title = str(settings.get("UI_DISPLAY_TITLE", "")).strip() or title_default
        self._display_subtitle = str(settings.get("UI_DISPLAY_SUBTITLE", "")).strip() or subtitle_default

        year_options = settings.get("UI_YEAR_OPTIONS", list(DEFAULT_YEAR_OPTIONS))
        self._year_options = self._sanitize_year_options(year_options)
        default_year = str(settings.get("UI_DEFAULT_YEAR", DEFAULT_DEFAULT_YEAR)).strip()
        self._default_year = default_year if default_year in self._year_options else self._year_options[0]

    def _sanitize_year_options(self, values):
        valid = []
        for item in values if isinstance(values, list) else []:
            year = str(item).strip()
            if len(year) == 4 and year.isdigit() and year not in valid:
                valid.append(year)
        if not valid:
            valid = list(DEFAULT_YEAR_OPTIONS)
        return valid

    def _setup_ui(self):
        app_info = get_app_info()
        app_name = app_info.get("app_name", "App")
        self.setWindowTitle(f"{app_name}")
        self.resize(760, 520)

        root = QWidget(self)
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        self.title_label = QLabel(self._display_title)
        layout.addWidget(self.title_label)
        self.subtitle_label = QLabel(self._display_subtitle)
        layout.addWidget(self.subtitle_label)

        input_row = QHBoxLayout()
        layout.addLayout(input_row)

        self.year_combo = QComboBox()
        self.year_combo.addItems(self._year_options)
        self.year_combo.setCurrentText(self._default_year)
        self.year_combo.currentTextChanged.connect(self._update_case_id_preview)
        input_row.addWidget(self.year_combo)

        self.case_number_input = QLineEdit()
        self.case_number_input.setPlaceholderText("Case number")
        self.case_number_input.textChanged.connect(self._update_case_id_preview)
        self.case_number_input.returnPressed.connect(self._start_import)
        input_row.addWidget(self.case_number_input)

        self.case_id_preview = QLabel("")
        layout.addWidget(self.case_id_preview)

        top_controls_row = QHBoxLayout()
        layout.addLayout(top_controls_row)

        self.import_button = QPushButton("Import Case")
        self.import_button.clicked.connect(self._start_import)
        top_controls_row.addWidget(self.import_button, alignment=Qt.AlignmentFlag.AlignLeft)

        top_controls_row.addStretch(1)

        self.logo_label = QLabel("")
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        top_controls_row.addWidget(self.logo_label, stretch=2)

        top_controls_row.addStretch(1)

        right_stack = QVBoxLayout()
        self.settings_button = QPushButton("Settings")
        self.settings_button.clicked.connect(self._open_settings_dialog)
        self.settings_button.setMaximumWidth(150)
        right_stack.addWidget(self.settings_button)

        self.check_update_button = QPushButton("Check for Update")
        self.check_update_button.clicked.connect(self._open_update_check_dialog)
        self.check_update_button.setMaximumWidth(150)
        right_stack.addWidget(self.check_update_button)

        self.advanced_settings_button = QPushButton("Advanced Settings")
        self.advanced_settings_button.clicked.connect(self._open_advanced_settings_guarded)
        self.advanced_settings_button.setMaximumWidth(150)
        right_stack.addWidget(self.advanced_settings_button)

        self.color_mode_button = QPushButton("")
        self.color_mode_button.clicked.connect(self._toggle_color_mode)
        self.color_mode_button.setMaximumWidth(150)
        right_stack.addWidget(self.color_mode_button)
        right_stack.addStretch(1)
        top_controls_row.addLayout(right_stack)

        logs_row = QHBoxLayout()
        layout.addLayout(logs_row, stretch=1)

        summary_col = QVBoxLayout()
        self.summary_log_title = QLabel("Case Summary")
        summary_col.addWidget(self.summary_log_title)
        self.summary_log_output = QTextEdit()
        self.summary_log_output.setReadOnly(True)
        summary_col.addWidget(self.summary_log_output, stretch=1)
        logs_row.addLayout(summary_col, stretch=1)

        process_col = QVBoxLayout()
        self.process_log_title = QLabel("Process Log")
        process_col.addWidget(self.process_log_title)
        self.process_log_output = QTextEdit()
        self.process_log_output.setReadOnly(True)
        process_col.addWidget(self.process_log_output, stretch=1)
        logs_row.addLayout(process_col, stretch=1)

        self._refresh_color_mode_button_text()
        self._apply_visual_style()
        self._update_logo_display()
        self._append_log("Ready for case ID input.")
        self._update_case_id_preview()

    def _update_case_id_preview(self):
        case_id = build_case_id(self.year_combo.currentText(), self.case_number_input.text())
        self.case_id_preview.setText(f"Case ID: {case_id}")

    def _append_log(self, message):
        self._append_routed_message(str(message))

    def _append_routed_message(self, msg):
        msg = str(msg)
        to_summary, to_process = self._route_log_panels(msg)
        if to_summary:
            self._append_to_panel(self.summary_log_output, msg)
        if to_process:
            self._append_to_panel(self.process_log_output, msg)

    def _append_to_panel(self, panel, msg):
        escaped = html.escape(msg)
        tag = self._detect_log_tag(msg)
        if self._color_mode:
            theme = THEMES.get(self._theme_name, THEMES["Default"])
            color = theme["log_colors"].get(tag, theme["log_colors"]["default"])
            rendered = f'<span style="color:{color};">{escaped}</span>'
        else:
            rendered = f"<span>{escaped}</span>"
        panel.append(rendered)

    def _route_log_panels(self, message):
        msg = message.strip()

        # Left panel: Case Summary (exact list requested)
        if (
            msg.startswith("Pt: ")
            or msg.startswith("🦷 Tooth = ")
            or msg == "👤 SIGNATURE DR"
            or msg == "🖋 HAS A STUDY"
            or msg == "🧪 HAS A STUDY"
            or msg == "❌ NO STUDY AVAILABLE"
            or msg == "ANTERIOR"
            or msg == "🧱 MODELESS CASE (Argen)"
            or msg == "🏭 ARGEN CASE"
            or msg == "🧑‍🎓 DESIGNER CASE"
            or msg == "🧑‍🎓 SERBIA CASE"
            or msg == "🤖 DESIGNER CASE"
            or msg == "🤖 SERBIA CASE"
            or msg == "Itero Case"
            or msg == "Itero Case (fallback)"
            or msg.startswith("🦷 Detected teeth: ")
            or msg == "🦷 EVO reports units > 1"
            or msg == "❌ Multiple units — manual import required"
            or msg.startswith("❌ Manual import required — material: ")
            or msg == "❌ Manual import required — unsupported material (not Envision/Adzir)"
            or msg == "❌ Manual import required — material"
            or msg == "🟡 JOTFORM CASE, requires manual import"
        ):
            return True, False

        # Right panel: Process Log (exact list requested + safe default)
        if (
            msg == "Ready for case ID input."
            or msg.startswith("Queued case: ")
            or msg == "--------------------------------------------"
            or msg.startswith("Starting import: ")
            or msg.startswith("📦 Starting import: ")
            or msg.startswith("📁 Found matching folder in ")
            or msg.startswith("📁 (fallback) Found matching folder in ")
            or msg.startswith("📄 Using template: ")
            or msg.startswith("📦 Created zip: ")
            or msg.startswith("🧹 Removed unzipped folder: ")
            or msg.startswith("⚠️ Could not remove existing zip: ")
            or msg.startswith("⚠️ Failed to remove unzipped folder: ")
            or msg.startswith("⚠️ Timeout warning: Case ")
            or msg.startswith("Error while importing: ")
            or msg.startswith("Finished: ")
            or msg == "Queue empty."
            or (msg.startswith("Completed ") and "→" in msg)
        ):
            return False, True

        # Preserve all existing messages: any unmatched line still goes to Process Log.
        return False, True

    def _detect_log_tag(self, message):
        lower = message.lower()
        if "✅" in message or "success" in lower:
            return "success"
        if "❌" in message or "error" in lower or "failed" in lower:
            return "error"
        if "⚠" in message or "warning" in lower or "timeout" in lower:
            return "warn"
        if "📦" in message or "processing" in lower or "info" in lower:
            return "info"
        if "has a study" in lower:
            return "has_study"
        if "signature" in lower:
            return "signature"
        if "tooth" in lower:
            return "tooth"
        if "shade" in lower:
            return "shade"
        if "template" in lower:
            return "template"
        if "case" in lower and any(x in lower for x in ["ai", "argen", "designer", "serbia"]):
            return "route"
        return "default"

    def _start_import(self):
        year = self.year_combo.currentText()
        case_number = self.case_number_input.text()
        case_id = build_case_id(year, case_number)

        if not validate_case_id(case_id):
            QMessageBox.warning(self, "Invalid Case ID", "Please enter a valid case ID.")
            return

        self._case_queue.append(case_id)
        self._append_log(f"Queued case: {case_id}")
        self.case_number_input.clear()
        if self._active_case_id is None:
            self._start_next_import()

    def _start_next_import(self):
        if self._active_case_id is not None:
            return
        if not self._case_queue:
            self._append_log("Queue empty.")
            return

        case_id = self._case_queue.popleft()
        self._active_case_id = case_id
        self._append_to_panel(self.summary_log_output, case_id)
        self._append_log("--------------------------------------------")
        self._append_log(f"Starting import: {case_id}")

        self._worker = ImportWorker(case_id)
        self._thread = QThread(self)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.log.connect(self._append_log)
        self._worker.error.connect(self._on_import_error)
        self._worker.finished.connect(self._on_import_finished)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._clear_thread_refs)

        self._start_timeout_timer(case_id)
        self._thread.start()

    def _start_timeout_timer(self, case_id):
        if self._timeout_timer is not None:
            self._timeout_timer.stop()
            self._timeout_timer.deleteLater()
        self._timeout_timer = QTimer(self)
        self._timeout_timer.setSingleShot(True)
        self._timeout_timer.timeout.connect(lambda: self._warn_if_still_running(case_id))
        self._timeout_timer.start(60000)

    def _warn_if_still_running(self, case_id):
        if self._active_case_id == case_id and self._thread is not None:
            self._append_log(f"⚠️ Timeout warning: Case {case_id} has been running over 60 seconds.")

    def _on_import_error(self, error_message):
        self._append_log(f"Error while importing: {error_message}")

    def _on_import_finished(self):
        if self._timeout_timer is not None:
            self._timeout_timer.stop()
            self._timeout_timer.deleteLater()
            self._timeout_timer = None

        finished_case = self._active_case_id
        self._active_case_id = None
        if finished_case:
            self._append_log(f"Finished: {finished_case}")
            self._append_to_panel(self.summary_log_output, "--------------------------------------------")

    def _clear_thread_refs(self):
        self._thread = None
        self._worker = None
        if self._case_queue:
            self._start_next_import()
        else:
            self._append_log("Queue empty.")

    def _open_settings_dialog(self):
        dialog = SettingsDialog(
            theme_name=self._theme_name,
            logo_name=self._logo_name,
            display_title=self._display_title,
            display_subtitle=self._display_subtitle,
            year_options=self._year_options,
            default_year=self._default_year,
            parent=self,
        )
        if dialog.exec() != QDialog.Accepted:
            return

        payload = dialog.settings_payload()
        try:
            save_settings_updates(payload)
        except Exception as exc:
            QMessageBox.warning(self, "Settings Error", f"Failed to save settings: {exc}")
            return

        self._apply_ui_preferences(payload)

    def _open_advanced_settings_guarded(self):
        if not current_user_is_admin():
            QMessageBox.warning(
                self,
                "Advanced Settings",
                "Admin login required to access advanced settings",
            )
            return

        dialog = AdvancedSettingsDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return

        payload = dialog.settings_payload()
        try:
            save_admin_settings_updates(payload)
        except Exception as exc:
            QMessageBox.warning(self, "Advanced Settings Error", f"Failed to save settings: {exc}")
            return

        QMessageBox.information(
            self,
            "Advanced Settings Saved",
            "Advanced settings saved to admin_settings.json.\nRestart the app for changes to fully apply.",
        )

    def _open_update_check_dialog(self):
        app_info = get_app_info()
        current_version = str(app_info.get("app_version", "0.0.0")).strip() or "0.0.0"
        dialog = UpdateCheckDialog(current_version=current_version, parent=self)
        dialog.exec()

    def _apply_ui_preferences(self, payload):
        theme_name = str(payload.get("UI_THEME", "Default")).strip()
        self._theme_name = theme_name if theme_name in THEMES else "Default"
        logo_name = str(payload.get("UI_LOGO", "ADS")).strip()
        self._logo_name = logo_name if logo_name in LOGOS else "ADS"

        self._display_title = str(payload.get("UI_DISPLAY_TITLE", "")).strip() or self._display_title
        self._display_subtitle = str(payload.get("UI_DISPLAY_SUBTITLE", "")).strip() or self._display_subtitle
        self.title_label.setText(self._display_title)
        self.subtitle_label.setText(self._display_subtitle)

        years = self._sanitize_year_options(payload.get("UI_YEAR_OPTIONS", self._year_options))
        default_year = str(payload.get("UI_DEFAULT_YEAR", self._default_year)).strip()
        if default_year not in years:
            default_year = years[0]
        self._year_options = years
        self._default_year = default_year

        current = self.year_combo.currentText().strip()
        self.year_combo.blockSignals(True)
        self.year_combo.clear()
        self.year_combo.addItems(self._year_options)
        if current in self._year_options:
            self.year_combo.setCurrentText(current)
        else:
            self.year_combo.setCurrentText(self._default_year)
        self.year_combo.blockSignals(False)
        self._update_case_id_preview()
        self._update_logo_display()
        self._apply_visual_style()

    def _toggle_color_mode(self):
        self._color_mode = not self._color_mode
        self._refresh_color_mode_button_text()
        self._apply_visual_style()
        try:
            save_settings_updates({"UI_COLOR_MODE": "color" if self._color_mode else "standard"})
        except Exception:
            pass

    def _refresh_color_mode_button_text(self):
        self.color_mode_button.setText("Color" if self._color_mode else "Standard")

    def _update_logo_display(self):
        self.logo_label.setText(LOGOS.get(self._logo_name, LOGOS["ADS"]))
        self._apply_logo_style()

    def _apply_logo_style(self):
        if self._color_mode:
            theme = THEMES.get(self._theme_name, THEMES["Default"])
            logo_color = theme["text"]
            if logo_color.startswith("#") and len(logo_color) == 7:
                r = int(logo_color[1:3], 16)
                g = int(logo_color[3:5], 16)
                b = int(logo_color[5:7], 16)
            else:
                r, g, b = (255, 255, 255)
        else:
            r, g, b = (0, 0, 0)

        logo_text = LOGOS.get(self._logo_name, LOGOS["ADS"])
        font_size = 12 if "\n" in logo_text else 24
        self.logo_label.setStyleSheet(
            f"background: transparent; border: none; color: rgba({r}, {g}, {b}, 110); font-size: {font_size}px; font-weight: 700;"
        )

    def _apply_visual_style(self):
        if not self._color_mode:
            self.setStyleSheet("")
            self._apply_readability_overrides()
            self._apply_logo_style()
            return

        theme = THEMES.get(self._theme_name, THEMES["Default"])
        self.setStyleSheet(
            f"""
            QWidget {{
                background-color: {theme['bg']};
                color: {theme['text']};
            }}
            QLineEdit, QComboBox, QListWidget, QTextEdit {{
                background-color: {theme['input_bg']};
                color: {theme['input_text']};
                border: 1px solid {theme['accent']};
                border-radius: 4px;
                padding: 4px;
            }}
            QDialog {{
                background-color: {theme['panel']};
            }}
            QPushButton {{
                background-color: {theme['button_bg']};
                color: {theme['button_text']};
                border: 1px solid {theme['accent']};
                border-radius: 4px;
                padding: 6px 10px;
            }}
            QPushButton:hover {{
                border: 1px solid {theme['button_text']};
            }}
            """
        )
        self._apply_readability_overrides()
        self._apply_logo_style()

    def _apply_readability_overrides(self):
        white_panel_style = "background-color: #ffffff; color: #111111;"
        self.summary_log_output.setStyleSheet(white_panel_style)
        self.process_log_output.setStyleSheet(white_panel_style)
        self.year_combo.setStyleSheet("background-color: #ffffff; color: #111111;")
        self.case_number_input.setStyleSheet("background-color: #ffffff; color: #111111;")

    def closeEvent(self, event):
        if self._active_case_id is not None or self._case_queue:
            QMessageBox.warning(
                self,
                "Import in Progress",
                "Cannot close program while import is in progress or queue is not empty.",
            )
            event.ignore()
            return
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
