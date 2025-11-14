import os
import json
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import requests
from urllib.parse import quote_plus

# ---------- Config ----------
SUPABASE_URL = os.environ.get('SUPABASE_URL')  # ex: https://xxxxx.supabase.co
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY')
FLASK_SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'change-me-123')

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise RuntimeError("Set SUPABASE_URL and SUPABASE_SERVICE_KEY in env")

REST_BASE = SUPABASE_URL.rstrip('/') + '/rest/v1'
HEADERS_ANON = {
    'apikey': SUPABASE_ANON_KEY,
    'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
    'Content-Type': 'application/json'
}
HEADERS_SERVICE = {
    'apikey': SUPABASE_SERVICE_KEY,
    'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
    'Content-Type': 'application/json'
}

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = FLASK_SECRET_KEY

# Helper: query users table
def supabase_get(table, params=None, headers=HEADERS_ANON):
    url = f"{REST_BASE}/{table}"
    if params:
        url += '?' + params
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()

def supabase_post(table, payload, headers=HEADERS_SERVICE):
    url = f"{REST_BASE}/{table}"
    resp = requests.post(url, headers=headers, data=json.dumps(payload))
    resp.raise_for_status()
    return resp.json()

def supabase_patch(table, payload, params, headers=HEADERS_SERVICE):
    url = f"{REST_BASE}/{table}?{params}"
    resp = requests.patch(url, headers=headers, data=json.dumps(payload))
    resp.raise_for_status()
    return resp

# ---------- Routes ----------
@app.route("/")
def index():
    return render_template("index.html")

# Login via backend: checks users table where approved = true
@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(force=True)
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify({"status":"error","msg":"Email e senha são obrigatórios"}), 400

    # get user by email
    params = f"email=eq.{quote_plus(email)}"
    users = supabase_get("users", params=params)
    if not users:
        return jsonify({"status":"error","msg":"Usuário não encontrado"}), 404

    user = users[0]
    if not user.get("approved"):
        return jsonify({"status":"error","msg":"Cadastro pendente. Aguarde aprovação do administrador."}), 403

    # compare password hash stored in 'password_hash'
    pwdhash = user.get("password_hash")
    if not pwdhash or not check_password_hash(pwdhash, password):
        return jsonify({"status":"error","msg":"Email ou senha incorretos"}), 401

    # store minimal session
    session['user'] = {"id": user.get("id"), "email": user.get("email"), "is_admin": user.get("is_admin", False)}
    return jsonify({"status":"ok", "user": session['user']})

# Register (creates a 'pending' user in users table). No approval yet.
@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json(force=True)
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify({"status":"error","msg":"Email e senha são obrigatórios"}), 400

    # check existing by email
    params = f"email=eq.{quote_plus(email)}"
    existing = supabase_get("users", params=params)
    if existing:
        return jsonify({"status":"error","msg":"Usuário já cadastrado"}), 409

    pwdhash = generate_password_hash(password)
    payload = [{
        "email": email,
        "password_hash": pwdhash,
        "is_admin": False,
        "approved": False
    }]
    try:
        supabase_post("users", payload)  # uses service key
        return jsonify({"status":"ok","msg":"Cadastro pendente. Aguarde aprovação do administrador."})
    except Exception as e:
        return jsonify({"status":"error","msg": str(e)}), 500

# Admin-only: list pending users
@app.route("/api/pending_users", methods=["GET"])
def api_pending_users():
    u = session.get('user')
    if not u or not u.get('is_admin'):
        return jsonify({"status":"error","msg":"Autorização necessária"}), 401
    params = "approved=eq.false"
    users = supabase_get("users", params=params, headers=HEADERS_ANON)
    return jsonify({"status":"ok", "pending": users})

# Admin-only: approve a user
@app.route("/api/approve_user", methods=["POST"])
def api_approve_user():
    u = session.get('user')
    if not u or not u.get('is_admin'):
        return jsonify({"status":"error","msg":"Autorização necessária"}), 401
    data = request.get_json(force=True)
    email = data.get("email")
    if not email:
        return jsonify({"status":"error","msg":"email required"}), 400
    params = f"email=eq.{quote_plus(email)}"
    try:
        resp = supabase_patch("users", {"approved": True}, params=params, headers=HEADERS_SERVICE)
        if resp.status_code in (200,204):
            return jsonify({"status":"ok","msg":"Usuário aprovado"})
        return jsonify({"status":"error","msg":"Falha ao aprovar"}), 500
    except Exception as e:
        return jsonify({"status":"error","msg": str(e)}), 500

# Logout
@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.pop('user', None)
    return jsonify({"status":"ok"})

# Check session
@app.route("/api/session", methods=["GET"])
def api_session():
    return jsonify({"user": session.get('user')})

# Simple route for backend-triggered IA run (optional)
@app.route("/api/run_ia", methods=["POST"])
def api_run_ia():
    u = session.get('user')
    if not u or not u.get('is_admin'):
        return jsonify({"status":"error","msg":"Autorização necessária"}), 401
    # Here you could call ia_completa.py logic or trigger a job
    # For now, just return ok placeholder
    return jsonify({"status":"ok","msg":"IA trigger placeholder"})

# ---------- Run ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
