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
