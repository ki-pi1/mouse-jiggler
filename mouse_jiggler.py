import ctypes
import ctypes.wintypes
import sys
import time
import pyautogui

INTERVAL = 30

_ES_CONTINUOUS       = 0x80000000
_ES_SYSTEM_REQUIRED  = 0x00000001
_ES_DISPLAY_REQUIRED = 0x00000002

_SW_RESTORE                   = 9
_SPI_GETFOREGROUNDLOCKTIMEOUT = 0x2000
_SPI_SETFOREGROUNDLOCKTIMEOUT = 0x2001

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
    """Gibt den Handle des ersten sichtbaren Citrix-Fensters zurück oder None."""
    results = []

    @_WNDENUMPROC
    def _cb(hwnd, _):
        if ctypes.windll.user32.IsWindowVisible(hwnd):
            buf = ctypes.create_unicode_buffer(256)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf, 256)
            if "citrix" in buf.value.lower():
                results.append(hwnd)
        return True

    ctypes.windll.user32.EnumWindows(_cb, 0)
    return results[0] if results else None


def _force_foreground(hwnd: int) -> None:
    """Bringt ein Fenster zuverlässig in den Vordergrund.

    SPI_SETFOREGROUNDLOCKTIMEOUT=0 deaktiviert die Windows-Foreground-Sperre
    kurzzeitig — dadurch greift SetForegroundWindow auch aus Hintergrundprozessen.
    """
    user32 = ctypes.windll.user32
    timeout = ctypes.c_uint(0)
    user32.SystemParametersInfoW(_SPI_GETFOREGROUNDLOCKTIMEOUT, 0, ctypes.byref(timeout), 0)
    user32.SystemParametersInfoW(_SPI_SETFOREGROUNDLOCKTIMEOUT, 0, 0, 0)
    user32.ShowWindow(hwnd, _SW_RESTORE)
    user32.BringWindowToTop(hwnd)
    user32.SetForegroundWindow(hwnd)
    user32.SystemParametersInfoW(_SPI_SETFOREGROUNDLOCKTIMEOUT, 0, timeout.value, 0)


def jiggle():
    ox, oy = pyautogui.position()

    # Lokales Jiggle
    pyautogui.moveRel(5, 0, duration=0)
    time.sleep(0.05)
    pyautogui.moveTo(ox, oy, duration=0)

    # Citrix-Jiggle: Fenster in den Vordergrund holen, jiggle, zurück
    citrix_found = False
    hwnd = _find_citrix_hwnd()
    if hwnd:
        citrix_found = True
        prev_hwnd = ctypes.windll.user32.GetForegroundWindow()

        left, top, right, bottom = _get_window_rect(hwnd)
        cx = (left + right) // 2
        cy = (top + bottom) // 2

        _force_foreground(hwnd)
        time.sleep(0.2)

        pyautogui.moveTo(cx, cy, duration=0.3)
        pyautogui.moveRel(10, 0, duration=0.2)
        time.sleep(1.0)
        pyautogui.moveRel(-10, 0, duration=0.2)
        pyautogui.moveTo(ox, oy, duration=0.3)

        _force_foreground(prev_hwnd)

    ts = time.strftime("%H:%M:%S")
    return f"{ts} {'[+Citrix]' if citrix_found else '[lokal]'}"


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
