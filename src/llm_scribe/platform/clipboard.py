import sys
import time
from typing import Optional

from llm_scribe.utils.logger import logger


def get_clipboard_text(root, root_hwnd: Optional[int] = None) -> Optional[str]:
    if sys.platform == "win32":
        return _get_clipboard_text_win32(root_hwnd or 0)
    return _get_clipboard_text_tk(root)


def _get_clipboard_text_tk(root) -> Optional[str]:
    for delay_s in (0.0, 0.01, 0.03):
        if delay_s:
            time.sleep(delay_s)
        try:
            content = root.clipboard_get()
            return content if content and content.strip() else None
        except Exception:
            continue
    return None


def _get_clipboard_text_win32(hwnd: int) -> Optional[str]:
    import ctypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    cf_unicode_text = 13

    user32.OpenClipboard.argtypes = [ctypes.c_void_p]
    user32.OpenClipboard.restype = ctypes.c_bool
    user32.GetClipboardData.argtypes = [ctypes.c_uint]
    user32.GetClipboardData.restype = ctypes.c_void_p
    user32.CloseClipboard.restype = ctypes.c_bool

    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalUnlock.restype = ctypes.c_bool

    opened = False
    try:
        if hwnd and user32.OpenClipboard(hwnd):
            opened = True
        else:
            time.sleep(0.01)
            if user32.OpenClipboard(0):
                opened = True
            else:
                return None

        h_clipboard_data = user32.GetClipboardData(cf_unicode_text)
        if not h_clipboard_data:
            return None

        p_data = kernel32.GlobalLock(h_clipboard_data)
        if not p_data:
            logger.error("Clipboard: GlobalLock failed.")
            return None

        try:
            content = ctypes.wstring_at(p_data)
            return content if content and content.strip() else None
        finally:
            kernel32.GlobalUnlock(h_clipboard_data)
    except Exception as e:
        logger.error(f"Clipboard: Win32 read failed: {e}")
        return None
    finally:
        if opened:
            user32.CloseClipboard()
