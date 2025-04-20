import requests
import json
from config_loader import load_config

def exchange_code_for_tokens(auth_code):
    config = load_config()
    oauth = config.get("zoho_projects_oauth", {})

    CLIENT_ID = oauth["client_id"]
    CLIENT_SECRET = oauth["client_secret"]
    PORT = oauth.get("app_port", 5001)
    REDIRECT_URI = f"http://localhost:{PORT}/callback"
    TOKEN_URL = "https://accounts.zoho.com/oauth/v2/token"
    params = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "code": auth_code
    }

    response = requests.post(TOKEN_URL, params=params)
    response.raise_for_status()
    tokens = response.json()
    return tokens

def save_tokens(tokens, filename="tokens.json"):
    with open(filename, "w") as f:
        json.dump(tokens, f, indent=2)

if __name__ == "__main__":
    auth_code = input("Enter the authorization code: ").strip()
    tokens = exchange_code_for_tokens(auth_code)
    save_tokens(tokens)
    print("Tokens have been saved to tokens.json")
