import os
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

usuarios = {
    "admin": {
        "senha": "281500",
        "admin": True
    }
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    usuario = data.get("usuario")
    senha = data.get("senha")

    if usuario in usuarios and usuarios[usuario]["senha"] == senha:
        return jsonify({
            "status": "ok",
            "usuario": usuario,
            "admin": usuarios[usuario]["admin"]
        })

    return jsonify({"status": "erro", "msg": "Usuário ou senha incorretos"})

@app.route("/criar_usuario", methods=["POST"])
def criar_usuario():
    data = request.json
    usuario = data.get("usuario")
    senha = data.get("senha")
    admin = data.get("admin", False)

    if usuario in usuarios:
        return jsonify({"status": "erro", "msg": "Usuário já existe"})

    usuarios[usuario] = {"senha": senha, "admin": admin}

    return jsonify({"status": "ok", "msg": "Usuário criado com sucesso"})

@app.route("/listar_usuarios")
def listar_usuarios():
    lista = [
        {"usuario": u, "admin": usuarios[u]["admin"]}
        for u in usuarios
    ]
    return jsonify(lista)

@app.route("/status")
def status():
    return jsonify({"status": "online"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
