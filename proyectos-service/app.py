from flask import Flask, request, jsonify
import json, os, requests

app = Flask(__name__)
DATA_FILE = "proyectos.json"
USUARIOS_URL = "http://usuarios-service:5001/usuarios"

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f: json.dump([], f)

@app.route("/proyectos", methods=["GET"])
def get_proyectos():
    with open(DATA_FILE) as f: return jsonify(json.load(f))

@app.route("/proyectos", methods=["POST"])
def add_proyecto():
    data = request.json
    # validar usuario existente
    usuarios = requests.get(USUARIOS_URL).json()
    if not any(u["id"] == data["usuario_id"] for u in usuarios):
        return jsonify({"error": "Usuario no encontrado"}), 400
    with open(DATA_FILE) as f: proyectos = json.load(f)
    data["id"] = len(proyectos) + 1
    proyectos.append(data)
    with open(DATA_FILE, "w") as f: json.dump(proyectos, f)
    return jsonify(data), 201

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
