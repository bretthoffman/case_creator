import html
import sys
from collections import deque

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
