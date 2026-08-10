from unittest.mock import patch
import mouse_jiggler

def test_jiggle_bewegt_maus_und_stellt_position_wieder_her():
    with patch("mouse_jiggler.pyautogui.position", return_value=(100, 200)) as mock_pos, \
         patch("mouse_jiggler.pyautogui.moveRel") as mock_rel, \
         patch("mouse_jiggler.pyautogui.moveTo") as mock_to, \
         patch("mouse_jiggler.time.sleep") as mock_sleep:
        result = mouse_jiggler.jiggle()
        mock_pos.assert_called_once()
        mock_rel.assert_called_once_with(1, 0, duration=0)
        mock_sleep.assert_called_once_with(0.1)
        mock_to.assert_called_once_with(100, 200, duration=0)
        assert isinstance(result, str)
        assert len(result) == 8  # Format "HH:MM:SS"
