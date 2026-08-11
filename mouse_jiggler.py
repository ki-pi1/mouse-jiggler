import ctypes
import ctypes.wintypes
import sys
import time
import pyautogui

INTERVAL = 30

_ES_CONTINUOUS       = 0x80000000
_ES_SYSTEM_REQUIRED  = 0x00000001
_ES_DISPLAY_REQUIRED = 0x00000002

_HWND_TOPMOST   = -1
_HWND_NOTOPMOST = -2
_SWP_NOSIZE     = 0x0001
_SWP_NOMOVE     = 0x0002
_SWP_NOACTIVATE = 0x0010

pyautogui.FAILSAFE = False

BANNER = """
╔══════════════════════════════════════╗
║         Mouse Jiggler aktiv          ║
║  Intervall: 30 s  |  Ctrl+C: Stopp  ║
╚══════════════════════════════════════╝
"""

_WNDENUMPROC = ctypes.WINFUNCTYPE(
    ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM
)


def _set_keep_awake(active: bool) -> None:
    flags = _ES_CONTINUOUS
    if active:
        flags |= _ES_SYSTEM_REQUIRED | _ES_DISPLAY_REQUIRED
    ctypes.windll.kernel32.SetThreadExecutionState(flags)


def _get_window_rect(hwnd):
    rect = ctypes.wintypes.RECT()
    ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return rect.left, rect.top, rect.right, rect.bottom


def _find_citrix_hwnd():
    """Sucht das sichtbare GDI+-Rendering-Fenster von Citrix.DesktopViewer (echte Session).
    Fallback: andere sichtbare Citrix-Fenster außer Notifications."""
    preferred = []
    fallback  = []
    _SKIP = {"benachrichtigung", "connection center"}

    @_WNDENUMPROC
    def _cb(hwnd, _):
        buf = ctypes.create_unicode_buffer(256)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, 256)
        title = buf.value.lower()
        if "citrix.desktopviewer" in title:
            preferred.append(hwnd)
        elif "citrix" in title and ctypes.windll.user32.IsWindowVisible(hwnd):
            if not any(s in title for s in _SKIP):
                fallback.append(hwnd)
        return True

    ctypes.windll.user32.EnumWindows(_cb, 0)
    return (preferred or fallback or [None])[0]


def _set_topmost(hwnd: int, topmost: bool) -> bool:
    """Setzt oder entfernt HWND_TOPMOST. Gibt True zurück wenn erfolgreich."""
    after = _HWND_TOPMOST if topmost else _HWND_NOTOPMOST
    ok = ctypes.windll.user32.SetWindowPos(
        hwnd, after, 0, 0, 0, 0,
        _SWP_NOSIZE | _SWP_NOMOVE | _SWP_NOACTIVATE,
    )
    return bool(ok)


def jiggle():
    ox, oy = pyautogui.position()

    # Lokales Jiggle
    pyautogui.moveRel(5, 0, duration=0)
    time.sleep(0.05)
    pyautogui.moveTo(ox, oy, duration=0)

    # Citrix-Jiggle
    citrix_status = "[lokal]"
    hwnd = _find_citrix_hwnd()
    if hwnd:
        left, top, right, bottom = _get_window_rect(hwnd)
        cx = (left + right) // 2
        cy = (top + bottom) // 2

        if _set_topmost(hwnd, True):
            time.sleep(0.1)
            pyautogui.moveTo(cx, cy, duration=0.3)
            pyautogui.moveRel(10, 0, duration=0.2)
            time.sleep(1.0)
            pyautogui.moveRel(-10, 0, duration=0.2)
            pyautogui.moveTo(ox, oy, duration=0.3)
            _set_topmost(hwnd, False)
            citrix_status = "[+Citrix OK]"
        else:
            err = ctypes.windll.kernel32.GetLastError()
            citrix_status = f"[Citrix ERR:{err}]"

    ts = time.strftime("%H:%M:%S")
    return f"{ts} {citrix_status}"


def main():
    print(BANNER)
    _set_keep_awake(True)
    last_jiggle = "—"
    try:
        while True:
            for remaining in range(INTERVAL, 0, -1):
                print(
                    f"\r  Nächste Bewegung in: {remaining:2d} s  |  Letzte: {last_jiggle}   ",
                    end="",
                    flush=True,
                )
                time.sleep(1)
            last_jiggle = jiggle()
    except KeyboardInterrupt:
        _set_keep_awake(False)
        print("\n\nBeendet. Maus-Jiggler gestoppt.")
        sys.exit(0)


if __name__ == "__main__":
    main()
