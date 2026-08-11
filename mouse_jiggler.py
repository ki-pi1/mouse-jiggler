import ctypes
import sys
import time
import pyautogui

INTERVAL = 30

# Windows Power-State-Flags
_ES_CONTINUOUS      = 0x80000000
_ES_SYSTEM_REQUIRED = 0x00000001
_ES_DISPLAY_REQUIRED = 0x00000002

pyautogui.FAILSAFE = False

BANNER = """
╔══════════════════════════════════════╗
║         Mouse Jiggler aktiv          ║
║  Intervall: 30 s  |  Ctrl+C: Stopp  ║
╚══════════════════════════════════════╝
"""


def _set_keep_awake(active: bool) -> None:
    """Teilt Windows direkt mit, Display und System wach zu halten (oder freizugeben)."""
    flags = _ES_CONTINUOUS
    if active:
        flags |= _ES_SYSTEM_REQUIRED | _ES_DISPLAY_REQUIRED
    ctypes.windll.kernel32.SetThreadExecutionState(flags)


def jiggle():
    x, y = pyautogui.position()
    pyautogui.moveRel(5, 0, duration=0)
    time.sleep(0.1)
    pyautogui.moveTo(x, y, duration=0)
    return time.strftime("%H:%M:%S")


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
