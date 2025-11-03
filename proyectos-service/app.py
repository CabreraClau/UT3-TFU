from flask import Flask, request, jsonify
import json, os, requests, time
import redis


app = Flask(__name__)

DATA_FILE = "proyectos.json"
USUARIOS_URL = "http://usuarios-service:5001/usuarios"
CIRCUIT_FILE = "circuit_state.json"

FAIL_THRESHOLD = 3
RESET_TIMEOUT = 10

cache = redis.Redis(host="redis", port=6379, decode_responses=True)
CACHE_TTL = 30  # segundos que los datos duran en cache

#  Crear archivo JSON si no existe 
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump([], f)



#  Inicializar archivo de circuito 
if not os.path.exists(CIRCUIT_FILE):
    with open(CIRCUIT_FILE, "w") as f:
        json.dump({"fail_count": 0, "circuit_open": False, "last_failure_time": 0}, f)


def read_circuit_state():
    with open(CIRCUIT_FILE) as f:
        return json.load(f)


def write_circuit_state(state):
    with open(CIRCUIT_FILE, "w") as f:
        json.dump(state, f)


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200

@app.route("/proyectos/<int:proyecto_id>", methods=["GET"])
def get_proyecto_by_id(proyecto_id):
    try:
        # 1️⃣ Buscar en cache
        cache_key = f"proyecto:{proyecto_id}"
        cached_proyecto = cache.get(cache_key)
        if cached_proyecto:
            print(f"Cache hit -> proyecto {proyecto_id}")
            return jsonify(json.loads(cached_proyecto)), 200

        # 2️⃣ Si no está en cache, leer del archivo
        print(f"Cache miss -> leyendo proyecto {proyecto_id} del archivo")
        with open(DATA_FILE) as f:
            proyectos = json.load(f)

        proyecto = next((p for p in proyectos if p["id"] == proyecto_id), None)
        if not proyecto:
            return jsonify({"error": "Proyecto no encontrado"}), 404

        # 3️⃣ Guardar en cache
        cache.setex(cache_key, CACHE_TTL, json.dumps(proyecto))

        return jsonify(proyecto), 200

    except Exception as e:
        print(f"Error al obtener proyecto: {e}")
        return jsonify({"error": "No se pudo obtener el proyecto"}), 500

@app.route("/proyectos", methods=["GET"])
def get_all_proyectos():
    try:
        with open(DATA_FILE) as f:
            proyectos = json.load(f)
        return jsonify({"data": proyectos}), 200
    except Exception as e:
        return jsonify({"error": f"No se pudieron obtener los proyectos: {str(e)}"}), 500


@app.route("/proyectos", methods=["POST"])
def add_proyecto():
    state = read_circuit_state()
    data = request.json

    if not data or not data.get("nombre") or not data.get("usuario_id"):
        return jsonify({"error": "Campos 'nombre' y 'usuario_id' son obligatorios"}), 400

    # --- Circuit Breaker Logic ---
    if state["circuit_open"]:
        if time.time() - state["last_failure_time"] < RESET_TIMEOUT:
            return jsonify({"error": "Circuito abierto: servicio de usuarios no disponible temporalmente"}), 503
        else:
            # Reinicia el circuito después del timeout
            state.update({"fail_count": 0, "circuit_open": False})
            write_circuit_state(state)

    try:
        response = requests.get(USUARIOS_URL, timeout=2)
        response.raise_for_status()
        usuarios = response.json().get("data", response.json())

        # Resetea el circuito si todo va bien
        state.update({"fail_count": 0, "circuit_open": False})
        write_circuit_state(state)

    except Exception:
        state["fail_count"] += 1
        state["last_failure_time"] = time.time()
        if state["fail_count"] >= FAIL_THRESHOLD:
            state["circuit_open"] = True
            print(" Circuit breaker abierto: demasiadas fallas en usuarios-service.")
        write_circuit_state(state)
        return jsonify({"error": "Servicio de usuarios no disponible"}), 503

    # Validar usuario existente
    if not any(u["id"] == data["usuario_id"] for u in usuarios):
        return jsonify({"error": "Usuario no encontrado"}), 400

    # Guardar proyecto
    with open(DATA_FILE) as f:
        proyectos = json.load(f)
    data["id"] = (proyectos[-1]["id"] + 1) if proyectos else 1
    proyectos.append(data)
    with open(DATA_FILE, "w") as f:
        json.dump(proyectos, f, indent=4)

    return jsonify({"mensaje": "Proyecto creado exitosamente", "data": data}), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
