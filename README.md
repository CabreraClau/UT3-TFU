# 🧩 Trabajo Final Unidad 3 – Soluciones Arquitectónicas

## 📘 Mini Gestor de Proyectos

Este proyecto implementa una **arquitectura de microservicios** utilizando **Flask** y **Docker**, con tres servicios independientes que se comunican entre sí mediante **HTTP interno**.

📹 [Aquí va un video explicativo del proyecto](https://drive.google.com/drive/folders/1vzmv4lIT7H1yjGgBBuUKAB06DZlHdZ-d?usp=sharing)

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

## 🏗️ Arquitectura aplicada

Partición por dominio funcional: cada microservicio representa un subdominio del sistema.

Escalabilidad horizontal: cada servicio puede ejecutarse en múltiples instancias.

Despliegue independiente: cada servicio se puede actualizar o reiniciar sin afectar a los demás.

Comunicación HTTP interna: mediante la red Docker.

Persistencia local: datos en formato JSON para simplicidad de la demo.

Disponibilidad básica: endpoint /health para monitoreo.

---

## 🔑 Patrón Valet Key (Valet Key Pattern)

El proyecto implementa el **Patrón Valet Key**, un patrón de seguridad donde en lugar de exponer credenciales completas o acceso total, se emiten tokens temporales con **permisos limitados y específicos** para recursos concretos.

### 🎯 Concepto

Similar a una llave de valet que solo permite conducir un auto (pero no abrir la guantera), los Valet Keys proporcionan acceso restringido con:

- **Permisos específicos** (scopes): `read:proyectos`, `write:usuarios`, etc.
- **Métodos HTTP limitados**: Solo GET, solo POST, etc.
- **Recursos restringidos**: Solo acceso a `proyecto_id=1`, o a `usuario_id` específicos
- **Expiración automática**: Los tokens expiran después de un tiempo configurado

### 📋 Scopes disponibles

| Scope | Descripción | Endpoints |
|-------|-------------|-----------|
| `read:usuarios` | Lectura de usuarios | GET `/usuarios` |
| `write:usuarios` | Escritura de usuarios | POST `/usuarios` |
| `read:proyectos` | Lectura de proyectos | GET `/proyectos/{id}` |
| `write:proyectos` | Escritura de proyectos | POST `/proyectos` |
| `read:tareas` | Lectura de tareas | GET `/tareas` |
| `write:tareas` | Escritura de tareas | POST `/tareas`, POST `/procesar_tareas` |

### 🚀 Uso del Patrón Valet Key

#### 1. Generar un token regular (requerido para crear Valet Keys)

```bash
# Generar token de API
curl -X POST http://localhost:5001/tokens
```

Respuesta:
```json
{
  "mensaje": "Token generado exitosamente",
  "token": "tu-token-aqui",
  "instrucciones": "..."
}
```

#### 2. Generar un Valet Key con permisos limitados

```bash
# Usar el token regular para generar un Valet Key
curl -X POST http://localhost:5001/valet-keys \
  -H "Authorization: Bearer tu-token-aqui" \
  -H "Content-Type: application/json" \
  -d '{
    "scopes": ["read:proyectos"],
    "allowed_methods": ["GET"],
    "resource_constraints": {
      "proyecto_id": 1
    },
    "expires_in_hours": 1
  }'
```

Respuesta:
```json
{
  "mensaje": "Valet Key generado exitosamente",
  "valet_key": "valet-key-token-aqui",
  "metadata": {
    "scopes": ["read:proyectos"],
    "allowed_methods": ["GET"],
    "resource_constraints": {
      "proyecto_id": 1
    },
    "expires_at": "2024-01-01T12:00:00"
  }
}
```

#### 3. Usar el Valet Key para acceder a recursos

```bash
# ✅ Esto funcionará - tiene permiso para leer proyecto_id=1
curl -X GET http://localhost:5002/proyectos/1 \
  -H "Authorization: Bearer valet-key-token-aqui"

# ❌ Esto fallará - no tiene permiso para proyecto_id=2
curl -X GET http://localhost:5002/proyectos/2 \
  -H "Authorization: Bearer valet-key-token-aqui"
# Respuesta: {"error": "Valet key solo tiene acceso a proyecto_id=1"}

# ❌ Esto fallará - no tiene permiso para POST
curl -X POST http://localhost:5002/proyectos \
  -H "Authorization: Bearer valet-key-token-aqui" \
  -d '{"nombre": "Nuevo proyecto"}'
# Respuesta: {"error": "Valet key no permite el método POST"}
```

### 📝 Ejemplos de Valet Keys

#### Ejemplo 1: Valet Key solo lectura para un proyecto específico
```json
{
  "scopes": ["read:proyectos"],
  "allowed_methods": ["GET"],
  "resource_constraints": {
    "proyecto_id": 1
  },
  "expires_in_hours": 2
}
```

#### Ejemplo 2: Valet Key para crear tareas en múltiples proyectos
```json
{
  "scopes": ["write:tareas"],
  "allowed_methods": ["POST"],
  "resource_constraints": {
    "proyecto_id": [1, 2, 3]
  },
  "expires_in_hours": 24
}
```

#### Ejemplo 3: Valet Key de solo lectura para usuarios (sin restricciones de recurso)
```json
{
  "scopes": ["read:usuarios"],
  "allowed_methods": ["GET"],
  "resource_constraints": {},
  "expires_in_hours": 1
}
```

### 🔒 Seguridad

- **Tokens regulares**: Acceso completo a todos los recursos (como antes)
- **Valet Keys**: Acceso limitado según permisos configurados
- **Expiración automática**: Los Valet Keys expiran y se eliminan de Redis automáticamente
- **Validación en cada request**: Cada endpoint valida permisos específicos
- **Tokens de servicio interno**: Para comunicación entre servicios (no expiran)

### 💡 Ventajas del Patrón Valet Key

1. **Principio de menor privilegio**: Solo se otorga el acceso mínimo necesario
2. **Seguridad mejorada**: Si un Valet Key se compromete, el daño es limitado
3. **Auditoría granular**: Puedes rastrear qué permisos específicos se usaron
4. **Control temporal**: Los tokens expiran automáticamente
5. **Flexibilidad**: Puedes crear tokens con diferentes niveles de acceso según necesidad

Apagar los contenedores
Ctrl + C
docker compose down



