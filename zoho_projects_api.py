import json
import re
from pathlib import Path
import requests
from config_loader import load_config
from zoho_projects_oauth_refresher import get_valid_token
from time import sleep
import markdown2

# ─── Constants ──────────────────────────────────────────────────────────────
DATA_FILE = Path(__file__).parent / "json" / "merge_requests.json"
TASKS_DUMP = Path(__file__).parent / "json" / "tasks.txt"
ISSUES_DUMP = Path(__file__).parent / "json" / "issues.txt"
_auth_token = None


# ─── Utilities ──────────────────────────────────────────────────────────────
def log(msg, level="INFO"):
    print(f"[{level}] {msg}")


def load_json_file(path: Path):
    try:
        with open(path, "r") as f:
            data = json.load(f)
        return data.get("merge_requests") if isinstance(data, dict) else data
    except Exception as e:
        raise SystemExit(f"fatal: failed to load JSON: {e}")


def get_headers():
    global _auth_token
    if not _auth_token:
        _auth_token = get_valid_token()
    return {"Authorization": f"Zoho-oauthtoken {_auth_token}"}


def build_api_url(config, endpoint, for_post=False):
    base = f"{config['zoho_projects_api_baseurl']}portal/{config['zoho_projects_portal_id']}"
    return (
        f"{base}/projects/{config['zoho_projects_project_id']}/{endpoint}"
        if for_post
        else f"{base}/{endpoint}"
    )


def api_get(url, params):
    try:
        return requests.get(url, headers=get_headers(), params=params, timeout=10)
    except requests.exceptions.RequestException as e:
        log(f"GET failed: {e}. Retrying...", "ERROR")
        sleep(2)
        try:
            return requests.get(url, headers=get_headers(), params=params, timeout=10)
        except requests.exceptions.RequestException as e2:
            log(f"GET retry failed: {e2}", "ERROR")
            return None


def api_post(url, payload):
    try:
        return requests.post(url, headers=get_headers(), json=payload, timeout=10)
    except requests.exceptions.RequestException as e:
        log(f"POST failed: {e}. Retrying...", "ERROR")
        sleep(2)
        try:
            return requests.post(url, headers=get_headers(), json=payload, timeout=10)
        except requests.exceptions.RequestException as e2:
            log(f"POST retry failed: {e2}", "ERROR")
            return None


# ─── API Callers ────────────────────────────────────────────────────────────
def get_tasks(config):
    url = build_api_url(config, "tasks")
    params = {
        "view_id": config["zoho_projects_tasks_view_id"],
        "page": 1,
        "per_page": 200,
    }
    resp = api_get(url, params)
    # if resp and resp.status_code == 200:
    #     log(f"Tasks response: {resp.json()}", "DEBUG")
    # else:
    #     log(f"Failed to get tasks: {resp.text}", "ERROR")
    return resp.json().get("tasks", []) if resp else []


def get_issues(config):
    url = build_api_url(config, "issues")
    params = {
        "view_id": config["zoho_projects_issues_view_id"],
        "page": 1,
        "per_page": 200,
    }
    resp = api_get(url, params)
    # if resp and resp.status_code == 200:
    #     log(f"Issues response: {resp.json()}", "DEBUG")
    # else:
    #     log(f"Failed to get issues: {resp.text}", "ERROR")
    return resp.json().get("issues", []) if resp else []


def post_to_zoho(config, endpoint, payload, dump_file):
    url = build_api_url(config, endpoint, for_post=True)
    resp = api_post(url, payload)

    with open(dump_file, "a") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")

    if resp is None:
        log(f"Failed to create {endpoint[:-1]}. Skipped.", "ERROR")
        return

    if resp.status_code // 100 != 2:  # status == 2xx
        log(f"Error creating {endpoint[:-1]}: {resp.text}", "ERROR")
    else:
        log(f"Created {endpoint[:-1]}: {payload['name']}", "CREATE")


# ─── Payload Builders ───────────────────────────────────────────────────────
def build_common_description(mr):
    mr_url = mr.get("web_url", "")
    mr_id = mr.get("iid", "")
    raw_desc = mr.get("description", "").strip()
    desc_html = markdown2.markdown(raw_desc) if raw_desc else ""

    return (
        f'<div>🔗 <a href="{mr_url}" target="_blank" rel="noopener noreferrer">'
        f"View MR</a> !{mr_id}<br><br></div>"
        f"<div>MR Description : {desc_html}</div>"
        if desc_html
        else ""
    )


def clean_title(mr, type_):
    prefix = (
        r"^\[?(patch|feat)\]?\s*[:\-]?\s*"
        if type_ == "task"
        else r"^\[?(bugfix|hotfix)\]?\s*[:\-]?\s*"
    )
    return re.sub(prefix, "", mr.get("title", ""), flags=re.IGNORECASE).strip()


def build_payload(mr, config, type_):
    title = clean_title(mr, type_)

    payload = {
        "name": title + " !" + str(mr.get("iid")),
        "description": build_common_description(mr),
    }

    if type_ == "task":
        status_map = config["zoho_projects_status_ids"][type_]
        payload["status"] = {"id": status_map.get(mr.get("state", "").lower(), 1)}
        payload["owners_and_work"] = {
            "owners": [{"add": [{"zpuid": config["zoho_projects_user_id"]}]}]
        }

    if type_ == "issue":
        payload["assignee"] = {"zpuid": config["zoho_projects_user_id"]}

    return payload


# ─── Main ────────────────────────────────────────────────────────────────────
def main():
    config = load_config()
    mrs = load_json_file(DATA_FILE)
    tasks = get_tasks(config)
    issues = get_issues(config)

    # Search in both name and description
    existing_ids = {
        match.group(1)
        for t in tasks + issues
        for field in ("description", "name")
        if (text := t.get(field)) and (match := re.search(r"!([0-9]+)", text))
    }

    for mr in mrs:
        mr_id = str(mr.get("iid"))
        title = mr.get("title", "").lower()

        if mr_id in existing_ids:
            log(f"MR already exists: !{mr_id}", "SKIP")
            continue

        if "patch" in title or "feat" in title:
            payload = build_payload(mr, config, "task")
            post_to_zoho(config, "tasks", payload, TASKS_DUMP)
        elif "bugfix" in title or "hotfix" in title:
            payload = build_payload(mr, config, "issue")
            post_to_zoho(config, "issues", payload, ISSUES_DUMP)
        else:
            log(f"Ignored MR (no match): {title}", "INFO")

    log("Sync complete ✅")


if __name__ == "__main__":
    main()
