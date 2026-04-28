# CASE CREATOR UPDATER LAUNCH FAILURE VISIBILITY REPORT

## 1. Summary of changes

The app now starts the updater via a small **`case_creator_updater.cmd`** wrapper in the same temp runner directory as the `.ps1` and job JSON. If **`powershell.exe -File`** returns a **non-zero** exit code (parse errors, early `exit 2`/`3`, `Fail-And-Exit`, etc.), the batch file prints a short hint and runs **`pause`** so the console stays open until the operator presses a key.

The PowerShell updater script writes an **`IMMEDIATE`** line to **`updater.log`** and prints a one-line console banner **before** `Add-Type` / joke data / heavy initialization. It validates **`-JobPath`** (non-empty, file exists) and **JSON load/parse** with dedicated **exit codes 2 and 3** and clear console + log messages.

The main app logs **`launcher=`**, **`script=`**, **`job=`**, **`subprocess_cwd=`**, **`comspec=`**, and the full **`subprocess argv`** as JSON before `Popen`. The post-launch Qt message is reworded so it is **not** implied that success is guaranteed—operators are pointed at the console behavior and **`updater.log`**.

## 2. Files modified

| File | Change |
|------|--------|
| `pyside6_ui.py` | `_write_updater_cmd_launcher`; `launch_external_updater` uses `COMSPEC /c launcher.cmd <job>`; extra `append_updater_client_log` for JSON argv; PS1 early log + path/JSON validation + single `$job` load; removed duplicate job read; `UpdateCheckDialog` copy updated. |
| `tests/test_updater_launch_workdir.py` | Asserts `Popen` argv uses `/c` and `case_creator_updater.cmd` + `.json` job. |
| `tests/test_updater_terminal_jokes_data.py` | Asserts embedded script contains `IMMEDIATE` bootstrap line. |
| `docs/reports/CASE_CREATOR_UPDATER_LAUNCH_FAILURE_VISIBILITY_REPORT.md` | This report. |

## 3. Root cause hypothesis

`powershell.exe -File` was launched **directly** with **`CREATE_NEW_CONSOLE`**. On **parse errors** or **terminating errors before** much of the script ran, PowerShell exited immediately with a **non-zero** code and the **console process exited**, so the window disappeared in a flash—especially while the Qt “updater started” dialog was still open, so the user never saw stderr or the few log lines that might have been written later in the script.

## 4. Launch visibility improvements

- **CMD wrapper** runs PowerShell and **`pause`** on **`if errorlevel 1`**, keeping the window open for early failures.
- **Console banner** at startup (`[Case Creator Updater] Started. Log: …`) even if later steps fail.
- **Qt dialog** explains that a **separate console** runs the updater, what **instant close** means, and where **`updater.log`** is.

## 5. Logging improvements

- **Client log** (before `Popen`): launcher path, script path, job path, `cwd`, `comspec`, and **`subprocess argv (JSON)`**.
- **Updater log** first line: `IMMEDIATE: Case Creator updater script entry (first line after param)`.
- **FATAL** lines for missing/empty job path and JSON parse failure before the rest of the pipeline runs.

## 6. Validation performed

- `python3 -m unittest tests.test_updater_launch_workdir tests.test_updater_terminal_jokes_data tests.test_updater_client_logging -v`
- **Manual Windows** run still recommended to confirm `pause` behavior and error text in the console.

## 7. Remaining risks or limitations

- Failures that **do not** set a non-zero PowerShell exit code are still hard to catch (unlikely for normal `exit` / throw paths).
- **`cmd /c`** still closes the console after **`pause`** when the user presses a key—that is intentional.
- Very early failures **before** the script runs (e.g. **powershell.exe** missing) depend on **cmd** output; the client log still records the intended argv.

## 8. Recommended next step

On Windows, trigger a **known-bad** job path or temporarily break the `.ps1` to confirm: console stays up, **`pause`** appears, and **`updater.log`** contains the **IMMEDIATE** line when the script at least starts.

---

## Final chat summary

1. **Launch inputs logged:** Yes — launcher, script, job, `cwd`, `comspec`, and JSON argv list in the client log before exit.
2. **Terminal stays visible on early failure:** Yes — non-zero PowerShell exit leads to **`pause`** in the `.cmd` wrapper (parse errors and scripted `exit 1/2/3` included).
3. **Early script/job failures diagnosable:** Yes — immediate log line, missing job + JSON errors to log and console with distinct exit codes.
4. **Retest on Windows:** Yes — full “Update Now” flow and a forced failure path.
