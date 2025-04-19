import json
import os
import requests
from pathlib import Path

# ─── Config Loading ───────────────────────────────────────────────────────────
CONFIG_FILE = Path(__file__).parent / 'config.json'

def loadConfig():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)     # json.load reads all key-value pairs
    except FileNotFoundError:
        raise SystemExit(f"fatal : config file not found: {CONFIG_FILE}")   # handle missing file
    except json.JSONDecodeError as e:
        raise SystemExit(f"fatal : invalid JSON in {CONFIG_FILE}: {e}")     # handle bad JSON

# ─── GitLab MR Fetching ───────────────────────────────────────────────────────
def fetch_mrs(token, state, baseurl, perPage=100):

    url = f"{baseurl}/merge_requests"
    headers = {"PRIVATE-TOKEN": token}
    params  = {"state": state, "PER_PAGE": perPage}
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()

def main():
    # 1) Load full config map
    config = loadConfig()            # returns dict with all values

    # 2) Extract needed values
    ACCESS_TOKEN    = config["gitlab_access_token"]
    GITLAB_API_BASEURL  = config["gitlab_api_baseurl"]
    PER_PAGE = config["gitlab_per_page"]

    # 3) Fetch and categorize
    result = {
        "open":   fetch_mrs(ACCESS_TOKEN, "opened", GITLAB_API_BASEURL, PER_PAGE),
        "merged": fetch_mrs(ACCESS_TOKEN, "merged", GITLAB_API_BASEURL, PER_PAGE),
        "closed": fetch_mrs(ACCESS_TOKEN, "closed", GITLAB_API_BASEURL, PER_PAGE),
    }

    # 4) Save to JSON
    out_file = Path(__file__).parent / 'mrs.json'
    with open(out_file, 'w') as fp:
        json.dump(result, fp, indent=2)  # human-readable dump

    print(f"Saved MR categories to {out_file}")

if __name__ == "__main__":
    main()
