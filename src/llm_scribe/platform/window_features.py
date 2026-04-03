import sys


def supports_click_through() -> bool:
    return sys.platform == "win32"


def set_click_through(window, enable: bool) -> bool:
    if sys.platform != "win32":
        return False

    import ctypes

    user32 = ctypes.windll.user32

    gwl_exstyle = -20
    ws_ex_layered = 0x00080000
    ws_ex_transparent = 0x00000020
    swp_nomove = 0x0002
    swp_nosize = 0x0001
    swp_nozorder = 0x0004
    swp_framechanged = 0x0020

    hwnd = window.winfo_id()
    if not hwnd:
        return False

    styles = user32.GetWindowLongW(hwnd, gwl_exstyle)
    if enable:
        new_styles = styles | ws_ex_transparent | ws_ex_layered
    else:
        new_styles = styles & ~ws_ex_transparent

    if styles == new_styles:
        return True

    user32.SetWindowLongW(hwnd, gwl_exstyle, new_styles)
    user32.SetWindowPos(
        hwnd,
        0,
        0,
        0,
        0,
        0,
        swp_nomove | swp_nosize | swp_nozorder | swp_framechanged,
    )
    return True
