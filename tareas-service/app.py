from flask import Flask, request, jsonify
import json, os, requests

app = Flask(__name__)
DATA_FILE = "tareas.json"
PROYECTOS_URL = "http://proyectos-service:5002/proyectos"

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f: json.dump([], f)

@app.route("/tareas", methods=["GET"])
def get_tareas():
    with open(DATA_FILE) as f: return jsonify(json.load(f))

@app.route("/tareas", methods=["POST"])
def add_tarea():
    data = request.json
    proyectos = requests.get(PROYECTOS_URL).json()
    if not any(p["id"] == data["proyecto_id"] for p in proyectos):
        return jsonify({"error": "Proyecto no encontrado"}), 400
    with open(DATA_FILE) as f: tareas = json.load(f)
    data["id"] = len(tareas) + 1
    tareas.append(data)
    with open(DATA_FILE, "w") as f: json.dump(tareas, f)
    return jsonify(data), 201

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003)
