import os


def current_user_is_admin() -> bool:
    """
    Return True only when the current user has admin rights on Windows.
    Fail safe (False) on non-Windows or any detection error.
    """
    if os.name != "nt":
        return False

    try:
        import ctypes

        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False
