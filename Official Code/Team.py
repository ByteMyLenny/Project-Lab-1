# Team.py
COLORS = ("MAGENTA", "YELLOW", "CYAN")
_color = None

def set_color(color):
    global _color
    color = color.upper()
    if color not in COLORS:
        raise ValueError("Unknown team color: " + color)
    _color = color

def get_color():
    return _color