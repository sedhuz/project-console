import json
from pathlib import Path
import requests
from config_loader import loadConfig
from zoho_projects_oauth_refresher import get_valid_token

# ─── Data Loading ───────────────────────────────────────────────────────────
DATA_FILE = Path(__file__).parent / "merge_requests.json"


def load_merge_requests(path: Path):
    try:
        with open(path, "r") as f:
            data = json.load(f)
        # expect top-level key 'merge_requests' or raw array
        return data.get("merge_requests") if isinstance(data, dict) else data
    except Exception as e:
        raise SystemExit(f"fatal: failed to load MR data: {e}")


# ─── Zoho Projects OAuth Call ────────────────────────────────────────────────
def list_zoho_projects(config):
    access_token = get_valid_token()
    endpoint = f"{config['zoho_projects_api_baseurl']}portal/{config['zoho_projects_portal_id']}/tasks"
    headers = { "Authorization": f"Zoho-oauthtoken {access_token}" }
    resp = requests.get(endpoint, headers=headers)
    return resp.json()


# ─── Main ────────────────────────────────────────────────────────────────────
def main():
    # load config + MR data
    config = loadConfig()
    merge_requests = load_merge_requests(DATA_FILE)

    # print merge requests
    print("Merge Requests:")
    for mr in merge_requests:
        print(f"- {mr['title']} (#{mr['id']})")
    print()

    # call Zoho Projects
    print("Requesting Zoho Projects API...")
    response = list_zoho_projects(config)

    # show raw response
    print(json.dumps(response, indent=2))


if __name__ == "__main__":
    main()
