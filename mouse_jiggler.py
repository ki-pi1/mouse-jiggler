import ctypes
import ctypes.wintypes
import sys
import time
import pyautogui

INTERVAL = 30

_ES_CONTINUOUS       = 0x80000000
_ES_SYSTEM_REQUIRED  = 0x00000001
_ES_DISPLAY_REQUIRED = 0x00000002

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


def _find_citrix_rect():
    """Gibt (left, top, right, bottom) des ersten sichtbaren Citrix-Fensters zurück oder None."""
    results = []

    @_WNDENUMPROC
    def _cb(hwnd, _):
        if ctypes.windll.user32.IsWindowVisible(hwnd):
            buf = ctypes.create_unicode_buffer(256)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf, 256)
            if "citrix" in buf.value.lower():
                rect = ctypes.wintypes.RECT()
                ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
                results.append((rect.left, rect.top, rect.right, rect.bottom))
        return True

    ctypes.windll.user32.EnumWindows(_cb, 0)
    return results[0] if results else None


def jiggle():
    ox, oy = pyautogui.position()

    # Lokales Jiggle
    pyautogui.moveRel(5, 0, duration=0)
    time.sleep(0.05)
    pyautogui.moveTo(ox, oy, duration=0)

    # Citrix-Jiggle: Maus kurz in die Fenstermitte, dann zurück
    citrix_found = False
    rect = _find_citrix_rect()
    if rect:
        citrix_found = True
        cx = (rect[0] + rect[2]) // 2
        cy = (rect[1] + rect[3]) // 2
        pyautogui.moveTo(cx, cy, duration=0)
        pyautogui.moveRel(5, 0, duration=0)
        time.sleep(0.05)
        pyautogui.moveRel(-5, 0, duration=0)
        pyautogui.moveTo(ox, oy, duration=0)

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
