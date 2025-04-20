import json
from pathlib import Path
import requests

TOKENS_FILE = Path(__file__).parent / "tokens.json"

# ─── Load Tokens ─────────────────────────────────────────────────────────────
def load_tokens():
    try:
        with open(TOKENS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        raise SystemExit(f"fatal: failed to load tokens: {e}")


# ─── Save Tokens ─────────────────────────────────────────────────────────────
def save_tokens(data):
    try:
        with open(TOKENS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        raise SystemExit(f"fatal: failed to save tokens: {e}")


# ─── Refresh Access Token ─────────────────────────────────────────────────────
def refresh_access_token(tokens):
    url = "https://accounts.zoho.com/oauth/v2/token"
    payload = {
        "refresh_token": tokens["refresh_token"],
        "client_id": tokens["client_id"],
        "client_secret": tokens["client_secret"],
        "grant_type": "refresh_token",
    }
    resp = requests.post(url, data=payload)
    if resp.status_code != 200:
        raise SystemExit(f"fatal: failed to refresh token: {resp.text}")

    new_data = resp.json()
    tokens["access_token"] = new_data["access_token"]
    save_tokens(tokens)
    print("✔ Access token refreshed.")
    return tokens


# ─── Get Valid Token ──────────────────────────────────────────────────────────
def get_valid_token():
    tokens = load_tokens()
    # ping a test endpoint
    headers = {"Authorization": f"Zoho-oauthtoken {tokens['access_token']}"}
    test_url = "https://projectsapi.zoho.com/restapi/portal/"  # harmless GET
    test_resp = requests.get(test_url, headers=headers)

    if test_resp.status_code == 401:
        print("⚠ Token expired, refreshing...")
        tokens = refresh_access_token(tokens)

    return tokens["access_token"]
