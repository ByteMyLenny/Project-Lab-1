# Sampling.py
import json

FILE = "color_samples.json"      # default file (used by ColorSensor)

def _color_default():
    return {"white": {"red": 1.0, "green": 1.0, "blue": 1.0}, "samples": {}}

def save(data, file=FILE):
    """Write data (a dict) to a JSON file on the Pico."""
    with open(file, "w") as f:
        json.dump(data, f)

def load(file=FILE, default=None):
    """Read a JSON file from the Pico. Returns `default` if the file is missing or empty."""
    try:
        with open(file) as f:
            return json.load(f)
    except (OSError, ValueError):
        if default is not None:
            return default
        return _color_default() if file == FILE else {}