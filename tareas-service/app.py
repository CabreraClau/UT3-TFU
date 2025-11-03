from flask import Flask, request, jsonify
import json, os, requests, redis, time

app = Flask(__name__)

DATA_FILE = "tareas.json"
PROYECTOS_URL = "http://proyectos-service:5002/proyectos"

# 🔹 Conexión a Redis (cola de tareas)
queue = redis.Redis(host="redis", port=6379, decode_responses=True)
QUEUE_KEY = "tareas_pendientes"

# Crear archivo si no existe
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump([], f)


#  Endpoint salud  Health monitoring
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200


#  Obtener todas las tarea 
@app.route("/tareas", methods=["GET"])
def get_tareas():
    try:
        with open(DATA_FILE) as f:
            tareas = json.load(f)
        return jsonify({"data": tareas}), 200
    except Exception as e:
        return jsonify({"error": f"Error al leer tareas: {str(e)}"}), 500


#  Encolar nueva tarea 
@app.route("/tareas", methods=["POST"])
def enqueue_tarea():
    try:
        data = request.json

        # Chequear los campos requeridos
        if not data or not data.get("nombre") or not data.get("proyecto_id"):
            return jsonify({"error": "Campos 'nombre' y 'proyecto_id' son obligatorios"}), 400

        # Se consulta a los proyectos para validar que existan individualmente
        try:
            response = requests.get(f"{PROYECTOS_URL}/{data['proyecto_id']}", timeout=2)
            if response.status_code == 404:
                return jsonify({"error": "Proyecto no encontrado"}), 404
            response.raise_for_status()
        except Exception:
            return jsonify({"error": "Servicio de proyectos no disponible"}), 503

        # Enviar tarea a la cola (Redis)
        queue.rpush(QUEUE_KEY, json.dumps(data))
        print(f"📩 Tarea encolada: {data}")

        return jsonify({"mensaje": "Tarea encolada correctamente"}), 202

    except Exception as e:
        return jsonify({"error": f"No se pudo encolar la tarea: {str(e)}"}), 500


# Procesar todas las tareas pendientes 
@app.route("/procesar_tareas", methods=["POST"])
def procesar_tareas():
    procesadas = []
    while queue.llen(QUEUE_KEY) > 0:
        tarea_json = queue.lpop(QUEUE_KEY)
        if not tarea_json:
            break

        tarea = json.loads(tarea_json)
        print(f"⚙️ Procesando tarea: {tarea['nombre']}")
        time.sleep(2)  # simula tiempo de ejecución

        with open(DATA_FILE) as f:
            tareas = json.load(f)

        tarea["id"] = (tareas[-1]["id"] + 1) if tareas else 1
        tareas.append(tarea)

        with open(DATA_FILE, "w") as f:
            json.dump(tareas, f, indent=4)

        procesadas.append(tarea)

    return jsonify({"mensaje": "Tareas procesadas", "data": procesadas}), 200


#  Ejecutar la aplicación 
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003)
