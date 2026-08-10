import sys
import time
import pyautogui

INTERVAL = 30

pyautogui.FAILSAFE = False

BANNER = """
╔══════════════════════════════════════╗
║         Mouse Jiggler aktiv          ║
║  Intervall: 30 s  |  Ctrl+C: Stopp  ║
╚══════════════════════════════════════╝
"""

def jiggle():
    x, y = pyautogui.position()
    pyautogui.moveRel(1, 0, duration=0)
    time.sleep(0.1)
    pyautogui.moveTo(x, y, duration=0)
    return time.strftime("%H:%M:%S")


def main():
    print(BANNER)
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
        print("\n\nBeendet. Maus-Jiggler gestoppt.")
        sys.exit(0)


if __name__ == "__main__":
    main()
