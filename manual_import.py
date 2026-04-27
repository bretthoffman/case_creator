"""Compatibility shim; legacy manual import helpers live in legacy/manual_import.py."""
import importlib.util
from pathlib import Path

__all__ = [
    "extract_patient_name_from_3oxz",
    "find_drop_file",
    "find_evident_folder",
    "process_case_from_id",
]


def _load_impl():
    path = Path(__file__).resolve().parent / "legacy" / "manual_import.py"
    spec = importlib.util.spec_from_file_location("_manual_import_impl", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


_impl = _load_impl()
extract_patient_name_from_3oxz = _impl.extract_patient_name_from_3oxz
find_drop_file = _impl.find_drop_file
find_evident_folder = _impl.find_evident_folder
process_case_from_id = _impl.process_case_from_id
