from flask import Flask, request, jsonify
import json, os

app = Flask(__name__)
DATA_FILE = "usuarios.json"

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f: json.dump([], f)

@app.route("/usuarios", methods=["GET"])
def get_usuarios():
    with open(DATA_FILE) as f: return jsonify(json.load(f))

@app.route("/usuarios", methods=["POST"])
def add_usuario():
    data = request.json
    with open(DATA_FILE) as f: usuarios = json.load(f)
    data["id"] = len(usuarios) + 1
    usuarios.append(data)
    with open(DATA_FILE, "w") as f: json.dump(usuarios, f)
    return jsonify(data), 201

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
