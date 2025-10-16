# TP3 - API de Tareas Persistente con SQLite
# 📝 Descripción
API REST desarrollada con FastAPI que permite gestionar tareas de forma persistente usando SQLite como base de datos.

## 🔧 Requisitos Previos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)

## 📦 Instalación

### 1. Crear y activar entorno virtual

**En Git Bash / Linux / Mac:**
```bash
python -m venv venv
source venv/Scripts/activate  # En Windows Git Bash
# source venv/bin/activate    # En Linux/Mac
```

**En Windows CMD:**
```cmd
python -m venv venv
venv\Scripts\activate
```

### 2. Instalar dependencias
```bash
pip install fastapi uvicorn pydantic pytest httpx
```

## 🚀 Cómo iniciar el servidor
```bash
uvicorn main:app --reload
```

El servidor se iniciará en: **http://localhost:8000**

Verás un mensaje como:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
✅ Base de datos inicializada correctamente
```

## 📚 Acceder a la Documentación Interactiva

Una vez iniciado el servidor:
- **Swagger UI (recomendado)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Estas interfaces te permiten probar todos los endpoints directamente desde el navegador.

## 🎯 Endpoints Disponibles

### 1️⃣ Obtener información de la API
```http
GET http://localhost:8000/
```

### 2️⃣ Listar todas las tareas
```http
GET http://localhost:8000/tareas
```

**Query Parameters opcionales:**
- `estado`: `pendiente`, `en_progreso`, `completada`
- `texto`: Buscar en la descripción
- `prioridad`: `baja`, `media`, `alta`
- `orden`: `asc`, `desc` (por fecha de creación)

**Ejemplos:**
```bash
# Todas las tareas
curl http://localhost:8000/tareas

# Solo pendientes
curl http://localhost:8000/tareas?estado=pendiente

# Buscar "comprar"
curl http://localhost:8000/tareas?texto=comprar

# Prioridad alta, ordenadas descendente
curl http://localhost:8000/tareas?prioridad=alta&orden=desc

# Múltiples filtros combinados
curl http://localhost:8000/tareas?estado=pendiente&prioridad=alta&texto=urgente
```

### 3️⃣ Crear una nueva tarea
```http
POST http://localhost:8000/tareas
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "descripcion": "Completar el TP3",
  "estado": "pendiente",
  "prioridad": "alta"
}
```

**Campos:**
- `descripcion` (obligatorio): Texto de la tarea (mínimo 1 carácter, no puede ser solo espacios)
- `estado` (opcional): `"pendiente"`, `"en_progreso"` o `"completada"` (default: `"pendiente"`)
- `prioridad` (opcional): `"baja"`, `"media"` o `"alta"` (default: `"media"`)

**Ejemplo con curl:**
```bash
curl -X POST "http://localhost:8000/tareas" \
  -H "Content-Type: application/json" \
  -d '{
    "descripcion": "Estudiar FastAPI",
    "estado": "pendiente",
    "prioridad": "alta"
  }'
```

**Respuesta exitosa (201):**
```json
{
  "id": 1,
  "descripcion": "Estudiar FastAPI",
  "estado": "pendiente",
  "prioridad": "alta",
  "fecha_creacion": "2025-10-16 14:30:45.123456"
}
```

### 4️⃣ Actualizar una tarea
```http
PUT http://localhost:8000/tareas/{id}
Content-Type: application/json
```

**Body (JSON) - Todos los campos son opcionales:**
```json
{
  "descripcion": "Tarea actualizada",
  "estado": "completada",
  "prioridad": "media"
}
```

**Ejemplo con curl:**
```bash
curl -X PUT "http://localhost:8000/tareas/1" \
  -H "Content-Type: application/json" \
  -d '{"estado": "completada"}'
```

### 5️⃣ Eliminar una tarea
```http
DELETE http://localhost:8000/tareas/{id}
```

**Ejemplo con curl:**
```bash
curl -X DELETE "http://localhost:8000/tareas/1"
```

### 6️⃣ Obtener resumen de tareas
```http
GET http://localhost:8000/tareas/resumen
```

**Respuesta (200):**
```json
{
  "total_tareas": 10,
  "por_estado": {
    "pendiente": 5,
    "en_progreso": 3,
    "completada": 2
  },
  "por_prioridad": {
    "baja": 2,
    "media": 4,
    "alta": 4
  }
}
```

### 7️⃣ Completar todas las tareas
```http
PUT http://localhost:8000/tareas/completar_todas
```

## 🧪 Ejecutar los Tests
```bash
# Ejecutar todos los tests
pytest test_TP3.py -v

# Ejecutar un test específico
pytest test_TP3.py::test_crear_tarea -v
```

## 🗄️ Base de Datos

La aplicación crea automáticamente **tareas.db** con la siguiente estructura:

### Tabla: tareas
| Campo          | Tipo    | Restricciones          | Descripción                    |
|----------------|---------|------------------------|--------------------------------|
| id             | INTEGER | PRIMARY KEY AUTOINCREMENT | Identificador único          |
| descripcion    | TEXT    | NOT NULL               | Descripción de la tarea        |
| estado         | TEXT    | NOT NULL               | Estado: pendiente, en_progreso, completada |
| prioridad      | TEXT    | NOT NULL, DEFAULT 'media' | Prioridad: baja, media, alta |
| fecha_creacion | TEXT    | NOT NULL               | Fecha y hora de creación (con microsegundos) |

## ✅ Verificación de Persistencia

Para verificar que los datos persisten correctamente:

1. Iniciar el servidor: `uvicorn main:app --reload`
2. Crear algunas tareas
3. Detener el servidor (Ctrl+C)
4. Volver a iniciar: `uvicorn main:app --reload`
5. Listar las tareas: Las tareas seguirán allí ✅

## 📁 Estructura del Proyecto
```
TP3/
├── main.py           # Código principal de la API
├── test_TP3.py       # Tests automatizados
├── tareas.db         # Base de datos SQLite (se crea automáticamente)
├── README.md         # Este archivo
└── venv/             # Entorno virtual (no subir a GitHub)
```

## 🐛 Solución de Problemas

### El servidor no inicia
```bash
# Verifica que el entorno esté activado
source venv/Scripts/activate

# Verifica las dependencias
pip list | grep fastapi
```

### Error: "Address already in use"
```bash
uvicorn main:app --reload --port 8001
```

### Los tests fallan
```bash
rm tareas.db
pytest test_TP3.py -v
```

## 👨‍💻 Autor

Trabajo Práctico N°3 - Programación Backend  
**Fecha de Entrega:** 17 de Octubre de 2025 a las 21:00hs
```

---

## 📄 3. .gitignore (opcional pero recomendado)
```
# Entorno virtual
venv/
env/

# Archivos de Python
__pycache__/
*.py[cod]
*$py.class
*.so

# Cache de pytest
.pytest_cache/

# Base de datos (comentar si quieres subirla)
# tareas.db

# IDEs
.vscode/
.idea/
*.swp
*.swo

# Sistema operativo
.DS_Store
Thumbs.db