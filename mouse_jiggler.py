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
    """Findet das größte sichtbare Fenster von Citrix.DesktopViewer.App.exe anhand des Prozesses.
    Sucht nach Prozessname statt Fenstertitel, da der Viewer-Titel variiert."""
    _TARGET = "citrix.desktopviewer.app.exe"
    _PROCESS_QUERY = 0x1000  # PROCESS_QUERY_LIMITED_INFORMATION
    candidates = []

    @_WNDENUMPROC
    def _cb(hwnd, _):
        if not ctypes.windll.user32.IsWindowVisible(hwnd):
            return True
        pid = ctypes.c_ulong(0)
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        hproc = ctypes.windll.kernel32.OpenProcess(_PROCESS_QUERY, False, pid.value)
        if hproc:
            buf  = ctypes.create_unicode_buffer(512)
            size = ctypes.c_ulong(512)
            ctypes.windll.kernel32.QueryFullProcessImageNameW(hproc, 0, buf, ctypes.byref(size))
            ctypes.windll.kernel32.CloseHandle(hproc)
            if _TARGET in buf.value.lower():
                rect = ctypes.wintypes.RECT()
                ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
                w = rect.right - rect.left
                h = rect.bottom - rect.top
                if w > 200 and h > 200:
                    candidates.append((hwnd, w * h))
        return True

    ctypes.windll.user32.EnumWindows(_cb, 0)
    if candidates:
        candidates.sort(key=lambda x: -x[1])  # größtes Fenster = Hauptfenster
        return candidates[0][0]
    return None


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
