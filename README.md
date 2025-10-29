# 🧩 Trabajo Final Unidad 3 – Soluciones Arquitectónicas

## 📘 Mini Gestor de Proyectos

Este proyecto implementa una **arquitectura de microservicios** utilizando **Flask** y **Docker**, con tres servicios independientes que se comunican entre sí mediante **HTTP interno**.

---

## 🧱 Estructura general


UT3-TFU/
│
├── docker-compose.yml
│
├── usuarios-service/
│ ├── app.py
│ ├── Dockerfile
│ └── requirements.txt
│
├── proyectos-service/
│ ├── app.py
│ ├── Dockerfile
│ └── requirements.txt
│
└── tareas-service/
├── app.py
├── Dockerfile
└── requirements.txt


---

## ⚙️ Servicios

| Servicio | Puerto | Responsabilidad | Dependencias |
|-----------|---------|----------------|---------------|
| **usuarios-service** | 5001 | Gestiona usuarios (GET, POST) | — |
| **proyectos-service** | 5002 | Gestiona proyectos (GET, POST). Valida usuario existente llamando al servicio de usuarios. | usuarios-service |
| **tareas-service** | 5003 | Gestiona tareas (GET, POST). Valida proyecto existente llamando al servicio de proyectos. | proyectos-service |

Cada servicio persiste sus datos localmente en un archivo JSON.

---

## 🐳 Despliegue con Docker

### 🔧 Requisitos previos
- Tener instalado **Docker Desktop** o Docker Engine.
- No se necesita instalar Flask ni dependencias localmente (Docker se encarga).

### ▶️ Levantar la aplicación

Desde la raíz del proyecto:
```bash
docker compose up --build

Esto construye e inicia los tres servicios:
usuarios-service  -> http://localhost:5001
proyectos-service -> http://localhost:5002
tareas-service    -> http://localhost:5003

Cada uno tiene su propio contenedor y se comunican internamente mediante la red tfu3_network.
La respuesta esperada es: 
{"status": "ok"}

Flujo de uso
Crear un usuario
Invoke-RestMethod -Uri http://localhost:5001/usuarios -Method POST -Body '{"nombre":"Claudio"}' -ContentType "application/json"

Crear un proyecto (Valida el usuario)
Invoke-RestMethod -Uri http://localhost:5002/proyectos -Method POST -Body '{"nombre":"App UT3", "usuario_id":1}' -ContentType "application/json"

Crear una tarea (valida el proyecto)
Invoke-RestMethod -Uri http://localhost:5003/tareas -Method POST -Body '{"nombre":"Diseñar endpoints", "proyecto_id":1}' -ContentType "application/json"


Listar la informacion
Crear una tarea (valida el proyecto)

+--------------------+        +--------------------+        +--------------------+
|  usuarios-service  |        | proyectos-service  |        |  tareas-service    |
| (puerto 5001)      | <----> | (puerto 5002)      | <----> | (puerto 5003)      |
|  Maneja usuarios   |        | Valida usuarios    |        | Valida proyectos   |
+--------------------+        +--------------------+        +--------------------+
El usuario se crea en usuarios-service.

proyectos-service consulta internamente al usuarios-service para validar el usuario_id.

tareas-service consulta internamente al proyectos-service para validar el proyecto_id.

#Arquitectura aplicada

Partición por dominio funcional: cada microservicio representa un subdominio del sistema.

Escalabilidad horizontal: cada servicio puede ejecutarse en múltiples instancias.

Despliegue independiente: cada servicio se puede actualizar o reiniciar sin afectar a los demás.

Comunicación HTTP interna: mediante la red Docker.

Persistencia local: datos en formato JSON para simplicidad de la demo.

Disponibilidad básica: endpoint /health para monitoreo.

Apagar los contenedores
Ctrl + C
docker compose down



