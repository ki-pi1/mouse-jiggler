from unittest.mock import call, patch
import mouse_jiggler


def test_jiggle_lokal_ohne_citrix():
    with patch("mouse_jiggler.pyautogui.position", return_value=(100, 200)), \
         patch("mouse_jiggler.pyautogui.moveRel") as mock_rel, \
         patch("mouse_jiggler.pyautogui.moveTo") as mock_to, \
         patch("mouse_jiggler.time.sleep"), \
         patch("mouse_jiggler._find_citrix_rect", return_value=None):
        result = mouse_jiggler.jiggle()
        mock_rel.assert_called_once_with(5, 0, duration=0)
        mock_to.assert_called_once_with(100, 200, duration=0)
        assert "[lokal]" in result


def test_jiggle_mit_citrix_fenster():
    citrix_rect = (0, 0, 800, 600)  # cx=400, cy=300
    with patch("mouse_jiggler.pyautogui.position", return_value=(100, 200)), \
         patch("mouse_jiggler.pyautogui.moveRel") as mock_rel, \
         patch("mouse_jiggler.pyautogui.moveTo") as mock_to, \
         patch("mouse_jiggler.time.sleep"), \
         patch("mouse_jiggler._find_citrix_rect", return_value=citrix_rect):
        result = mouse_jiggler.jiggle()
        # Erstes moveRel: lokales Jiggle
        # Zweites/Drittes moveRel: Citrix-Jiggle (+5, -5)
        assert mock_rel.call_count == 3
        assert mock_rel.call_args_list[0] == call(5, 0, duration=0)
        assert mock_rel.call_args_list[1] == call(10, 0, duration=0.2)
        assert mock_rel.call_args_list[2] == call(-10, 0, duration=0.2)
        # moveTo: zurück zur Ausgangsposition + Citrix-Mitte + zurück zur Ausgangsposition
        assert mock_to.call_count == 3
        assert mock_to.call_args_list[0] == call(100, 200, duration=0)
        assert mock_to.call_args_list[1] == call(400, 300, duration=0.3)
        assert mock_to.call_args_list[2] == call(100, 200, duration=0.3)
        assert "[+Citrix]" in result
