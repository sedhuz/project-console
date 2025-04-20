from flask import Flask, request, redirect, render_template
import webbrowser
from config_loader import load_config


def load_settings():
    config = load_config()
    oauth = config.get("zoho_projects_oauth", {})
    return {
        "client_id": oauth.get("client_id"),
        "scopes": oauth.get("scopes", []),
        "port": oauth.get("app_port", 5001),
    }


settings = load_settings()
CLIENT_ID = settings["client_id"]
SCOPES = settings["scopes"]
PORT = settings["port"]
REDIRECT_URI = f"http://localhost:{PORT}/callback"
SCOPE_PARAM = "+".join(SCOPES)

auth_url = (
    "https://accounts.zoho.com/oauth/v2/auth"
    f"?scope={SCOPE_PARAM}&client_id={CLIENT_ID}"
    "&response_type=code&access_type=offline"
    f"&redirect_uri={REDIRECT_URI}&prompt=consent"
)

app = Flask(__name__, template_folder="templates", static_folder="static")


@app.route("/")
def home():
    app.logger.info("Homepage accessed")
    return render_template("home.html")


@app.route("/login")
def login():
    return redirect(auth_url)


@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return render_template("callback_err.html"), 400
    return render_template("callback.html", code=code)


if __name__ == "__main__":
    webbrowser.open(f"http://localhost:{PORT}/")
    app.run(host="0.0.0.0", port=PORT, debug=True, use_reloader=False)
