"""Root compatibility shim; legacy Tkinter UI implementation is legacy/import_gui.pyw."""
import runpy
from pathlib import Path

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parent / "legacy" / "import_gui.pyw"), run_name="__main__")
