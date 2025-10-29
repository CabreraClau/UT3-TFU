from flask import Flask, request, jsonify
import json, os

app = Flask(__name__)

DATA_FILE = "usuarios.json"


if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump([], f)

# verificar estado del servicio 
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200



@app.route("/usuarios", methods=["GET"])
def get_usuarios():
    try:
        with open(DATA_FILE) as f:
            usuarios = json.load(f)
        return jsonify({"data": usuarios}), 200
    except Exception as e:
        return jsonify({"error": f"Error al leer usuarios: {str(e)}"}), 500



@app.route("/usuarios", methods=["POST"])
def add_usuario():
    try:
        data = request.json


        if not data or not data.get("nombre"):
            return jsonify({"error": "El campo 'nombre' es obligatorio"}), 400

        with open(DATA_FILE) as f:
            usuarios = json.load(f)

      
        nuevo_id = (usuarios[-1]["id"] + 1) if usuarios else 1
        data["id"] = nuevo_id
        usuarios.append(data)

        with open(DATA_FILE, "w") as f:
            json.dump(usuarios, f, indent=4)

        return jsonify({
            "mensaje": "Usuario creado exitosamente",
            "data": data
        }), 201

    except Exception as e:
        return jsonify({"error": f"No se pudo crear el usuario: {str(e)}"}), 500



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
