import json
import os
import requests
from pathlib import Path
from config_loader import load_config


# ─── GitLab MR Fetching ───────────────────────────────────────────────────────
def fetchMergeRequests(token, state, baseurl, perPage=100):

    url = f"{baseurl}/merge_requests"
    headers = {"PRIVATE-TOKEN": token}
    if state == None or state == "":
        params = {"PER_PAGE": perPage}
    else:
        params = {"state": state, "PER_PAGE": perPage}
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()


def main():
    # 1) Load full config map
    config = load_config()  # returns dict with all values

    # 2) Extract needed values
    ACCESS_TOKEN = config["gitlab_access_token"]
    GITLAB_API_BASEURL = config["gitlab_api_baseurl"]
    PER_PAGE = config["gitlab_per_page"]

    # 3) Fetch and categorize
    result = {
        "merge_requests": fetchMergeRequests(
            ACCESS_TOKEN, None, GITLAB_API_BASEURL, PER_PAGE
        ),
    }

    # 4) Save to JSON
    out_file = Path(__file__).parent / "merge_requests.json"
    with open(out_file, "w") as fp:
        json.dump(result, fp, indent=2)  # human-readable dump

    print(f"Saved MR categories to {out_file}")


if __name__ == "__main__":
    main()
