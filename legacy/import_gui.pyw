import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
import threading
import os
import signal
import queue
from case_processor_final_clean import process_case_from_id as process_case
from flask import Flask, request, jsonify
from threading import Thread
from admin_access import current_user_is_admin
flask_app = Flask(__name__)

class CaseImporterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("3Shape Case Importer")
        self.root.configure(bg="#2b2b2b")  # Charcoal grey background
        # Top-right status display
        self.status_frame = tk.Frame(self.root, bg="#2b2b2b")
        self.status_frame.place(relx=1.0, y=5, anchor="ne")  # Top right corner

        # Rainbow "online" label in a row
        online_row = tk.Frame(self.status_frame, bg="#2b2b2b")
        online_row.pack(anchor="e")

        colors = ["red", "orange", "yellow", "green", "blue", "indigo", "violet"]
        for i, letter in enumerate("online"):
            lbl = tk.Label(online_row, text=letter, fg=colors[i % len(colors)],
                           bg="#111111", font=("Segoe UI", 8, "bold"))
            lbl.pack(side="left")

        # Ngrok link below
        self.ngrok_url_var = tk.StringVar(value="(Ngrok link not yet detected)")
        self.ngrok_entry = tk.Entry(self.status_frame, textvariable=self.ngrok_url_var,
                                    font=("Segoe UI", 7), fg="white", bg="#2b2b2b",
                                    relief="flat", state="readonly", justify="right", readonlybackground="#2b2b2b")
        self.ngrok_entry.pack(anchor="e")




        self.queue = queue.Queue()
        self.importing = False

        # Start background worker
        threading.Thread(target=self.process_queue, daemon=True).start()

        # Style configuration
        style = ttk.Style()
        style.theme_use("default")
        
        # Button
        style.configure("TButton", background="#3d3d3d", foreground="white",
                        font=("Segoe UI", 12), padding=6, borderwidth=0)
        style.map("TButton", background=[('active', '#ff1493')])
        
        # Labels & Entries
        style.configure("TLabel", background="#2b2b2b", foreground="white", font=("Segoe UI", 12))
        style.configure("TEntry", font=("Segoe UI", 16))
        
        # Combobox (dropdown) fully white including arrow area
        style.configure("TCombobox",
            fieldbackground="white",      # Input area
            background="white",           # Arrow button area
            foreground="black",           # Text inside
            selectbackground="white",
            selectforeground="black"
        )
        style.map("TCombobox",
            fieldbackground=[("readonly", "white")],
            background=[("readonly", "white")],
            foreground=[("readonly", "black")],
            arrowcolor=[("readonly", "black")]  # Ensures dropdown arrow stays visible
        )



        # Subheader
        self.subheader = ttk.Label(root, text="Kat's Single-Unit Scraper",
                                   font=("Segoe UI", 10, "italic"),
                                   foreground="lightgrey", background="#2b2b2b")
        self.subheader.pack(pady=(0, 5))

        # Case ID and YEAR selection row
        self.input_frame = ttk.Frame(root)

        self.year_var = tk.StringVar(value="2026")
        self.year_dropdown = ttk.Combobox(self.input_frame, textvariable=self.year_var, state="readonly",
                                           values=["2022", "2023", "2024", "2025", "2026", "2027"], width=6, font=("Segoe UI", 14))
        self.year_dropdown.pack(side="left", padx=(0, 10))

        self.case_id_entry = ttk.Entry(self.input_frame, width=12, font=("Segoe UI", 16), justify="left")
        self.case_id_entry.pack(side="left", ipadx=10)

        # Only pack the frame AFTER children are added
        self.input_frame.pack(pady=10)




        # Import button
        self.import_button = ttk.Button(root, text="Import Case", command=self.start_import)
        self.import_button.pack(pady=5)

        # Log output
        self.log_output = scrolledtext.ScrolledText(root, width=70, height=20, state='disabled',
                                                    font=("Segoe UI", 12), background="#f0f0f0", relief="flat")
        self.log_output.pack(pady=(10, 10))
        

        # Define tags (colors)
        self.log_output.tag_config("success", foreground="green")
        self.log_output.tag_config("has_study", foreground="lime green", font=("Segoe UI", 12, "bold"))
        self.log_output.tag_config("error", foreground="red")
        self.log_output.tag_config("warn", foreground="orange")
        self.log_output.tag_config("info", foreground="blue")
        self.log_output.tag_config("default", foreground="black")
        self.log_output.tag_config("signature", foreground="purple")
        self.log_output.tag_config("HAS A", foreground="red")
        self.log_output.tag_config("AVAILABLE", foreground="red")
        self.log_output.tag_config("ANTERIOR", foreground="blue")
        self.log_output.tag_config("evo", foreground="red")
        self.log_output.tag_config("tooth", foreground="blue")
        self.log_output.tag_config("shade", foreground="teal")        
        self.log_output.tag_config("template", foreground="#ffaa00")     # gold/yellow


        self.log_output.tag_config("route", foreground="#ff69b4")     # hot pink


        # Welcome message
        self.write_log("📥 Ready for case ID input.")

        # Bind Enter
        self.root.bind('<Return>', lambda event: self.start_import())

        # Prevent close during active processing
        self.root.protocol("WM_DELETE_WINDOW", self.force_quit)
        # Try to detect and show Ngrok URL
        self.root.after(1000, self.update_ngrok_url)


    def update_ngrok_url(self):
        try:
            import requests
            response = requests.get("http://127.0.0.1:4040/api/tunnels")
            data = response.json()
            public_url = data["tunnels"][0]["public_url"]
            self.ngrok_url_var.set(public_url)
        except Exception:
            self.ngrok_url_var.set("")

        # Keep polling every 15 seconds
        self.root.after(15000, self.update_ngrok_url)

    def write_log(self, message):
        tag = self.detect_tag(message)
        self.log_output.configure(state='normal')
        self.log_output.insert(tk.END, message + '\n', tag)
        self.log_output.yview(tk.END)
        self.log_output.configure(state='disabled')

    def detect_tag(self, message):
        lower = message.lower()
        if "✅" in message or "success" in lower:
            return "success"
        elif "❌" in message or "error" in lower or "failed" in lower:
            return "error"
        elif "⚠" in message or "missing" in lower or "warning" in lower:
            return "warn"
        elif "📦" in message or "processing" in lower or "info" in lower:
            return "info"
        elif "has a study" in lower:
            return "has_study"
        elif "signature" in lower:
            return "signature"
        elif "study" in lower:
            return "study"
        elif "tooth" in lower:
            return "tooth"
        elif "shade" in lower:
            return "shade"
        elif "template" in lower:
            return "template"
        elif "case" in lower and any(x in lower for x in ["ai", "argen", "designer", "serbia"]):
            return "route"
        else:
            return "default"


    def start_import(self):
        case_number = self.case_id_entry.get().strip()
        year = self.year_var.get()
        case_id = f"{year}-{case_number}"

        if not case_id:
            self.write_log("⚠️ Please enter a valid case ID.")
            return

        self.queue.put(case_id)
        self.write_log(f"📥 Queued case: {case_id}")
        self.case_id_entry.delete(0, tk.END)

    def process_queue(self):
        while True:
            case_id = self.queue.get()
            self.importing = True
            self.run_import(case_id)
            self.importing = not self.queue.empty()
            self.queue.task_done()

    def run_import(self, case_id):
        def target():
            try:
                self.write_log("--------------------------------------------")
                self.write_log(f"📦 Starting import: {case_id}")
                result = process_case(case_id, self.write_log)
                if isinstance(result, str) and "manual import required" in result.lower():
                    return  # Exit early without logging finished

            except Exception as e:
                self.write_log(f"❌ Unexpected error while importing {case_id}: {e}")

        import_thread = threading.Thread(target=target)
        import_thread.start()
        import_thread.join(timeout=60)

        if import_thread.is_alive():
            self.write_log(f"⏱️ Timeout: Case {case_id} took too long and was aborted.")
            # Note: Python can't truly "kill" a thread — you'd need to isolate it in a subprocess for that
        else:
            self.write_log(f"📁 Finished: {case_id}")


    def force_quit(self):
        if self.importing or not self.queue.empty():
            messagebox.showwarning("Import in Progress", "Cannot close program while import is in progress.")
            return
        self.write_log("🛑 Exiting...")
        self.root.update_idletasks()
        os.kill(os.getpid(), signal.SIGTERM)

    # Future integration point for Settings UI (PySide6 or Tkinter menu/button hook).
    # Intentionally not wired to a visible control yet to avoid broad UI changes.
    def request_advanced_settings_access(self):
        if not current_user_is_admin():
            messagebox.showwarning(
                "Advanced Settings",
                "Admin login required to access advanced settings"
            )
            return
        self._open_advanced_settings_placeholder()

    def _open_advanced_settings_placeholder(self):
        win = tk.Toplevel(self.root)
        win.title("Advanced Settings")
        win.configure(bg="#2b2b2b")
        tk.Label(
            win,
            text="Advanced settings placeholder",
            fg="white",
            bg="#2b2b2b",
            font=("Segoe UI", 10)
        ).pack(padx=16, pady=16)

@flask_app.route('/import-case', methods=['POST'])

def import_case():
    data = request.get_json()
    case_ids = data.get("case_ids", [])
    results = {}

    for cid in case_ids:
        logs = []

        def capture_log(msg):
            logs.append(msg)

        try:
            process_case(cid, capture_log)
            logs.append(f"📁 Finished: {cid}")
        except Exception as e:
            logs.append(f"❌ Error while importing {cid}: {e}")

        results[cid] = "\n".join(logs)

    return jsonify(results)


if __name__ == "__main__":
    # ✅ Start Flask server in background
    def start_flask():
        flask_app.run(port=5000)

    Thread(target=start_flask, daemon=True).start()

    root = tk.Tk()
    app = CaseImporterGUI(root)
    root.mainloop()


