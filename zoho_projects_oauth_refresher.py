import json
from pathlib import Path
import requests
import time
from config_loader import load_config

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

# ─── Retry Request Function ──────────────────────────────────────────────────
def request_with_retry(url, headers_func, retries=3, delay=2):
    for _ in range(retries):
        try:
            headers = headers_func()
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 401:
                print("⚠️ 401 Unauthorized, refreshing token...")
                refresh_access_token(load_tokens())
                continue
            resp.raise_for_status()
            return resp
        except requests.exceptions.RequestException as e:
            print(f"⚠ Error: {e}, retrying...")
            time.sleep(delay)
    raise SystemExit(f"fatal: failed after {retries} retries")


# ─── Refresh Access Token ─────────────────────────────────────────────────────
def refresh_access_token(tokens):
    config = load_config()
    oauth = config["zoho_projects_oauth"]

    payload = {
        "refresh_token": tokens["refresh_token"],
        "client_id": oauth["client_id"],
        "client_secret": oauth["client_secret"],
        "grant_type": "refresh_token",
    }

    url = "https://accounts.zoho.com/oauth/v2/token"
    resp = requests.post(url, data=payload)

    if resp.status_code != 200:
        error_msg = resp.json().get("error", "Unknown error")
        if "invalid_grant" in error_msg:
            raise SystemExit(f"fatal: refresh token invalid or expired: {error_msg}")
        raise SystemExit(f"fatal: failed to refresh token: {error_msg}")

    new_data = resp.json()
    tokens["access_token"] = new_data["access_token"]
    save_tokens(tokens)
    print("✅ Access token refreshed.")
    return tokens

# ─── Get Valid Token ──────────────────────────────────────────────────────────
def get_valid_token():
    tokens = load_tokens()
    headers = {"Authorization": f"Zoho-oauthtoken {tokens['access_token']}"}
    test_url = "https://projectsapi.zoho.com/api/v3/portal/548669/tasks"

    try:
        test_resp = requests.get(test_url, headers=headers, timeout=5)
        if test_resp.status_code == 401:
            raise Exception("Unauthorized")
        return tokens["access_token"]
    except:
        print("⚠️ Token expired, refreshing...")
        tokens = refresh_access_token(tokens)
        return tokens["access_token"]