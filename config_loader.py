import json
from pathlib import Path

# ─── Config Loading ───────────────────────────────────────────────────────────
CONFIG_FILE = Path(__file__).parent / "json" / "config.json"


def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)  # json.load reads all key-value pairs
    except FileNotFoundError:
        raise SystemExit(
            f"fatal : config file not found: {CONFIG_FILE}"
        )  # handle missing file
    except json.JSONDecodeError as e:
        raise SystemExit(
            f"fatal : invalid JSON in {CONFIG_FILE}: {e}"
        )  # handle bad JSON
