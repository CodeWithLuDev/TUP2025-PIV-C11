# TP3 - API de Tareas Persistente

## 📋 Descripción

API REST desarrollada con FastAPI que permite gestionar tareas de forma persistente utilizando SQLite como base de datos. Los datos se mantienen almacenados incluso después de reiniciar el servidor.

## 🚀 Características

- ✅ CRUD completo de tareas (Crear, Leer, Actualizar, Eliminar)
- ✅ Persistencia de datos con SQLite
- ✅ Filtros por estado, prioridad y texto
- ✅ Ordenamiento por fecha de creación
- ✅ Resumen de tareas por estado y prioridad
- ✅ Validación de datos con Pydantic
- ✅ Manejo de errores HTTP

## 📦 Instalación

### 1. Requisitos previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### 2. Instalar dependencias

```bash
pip install fastapi uvicorn
```

Para ejecutar los tests:

```bash
pip install pytest httpx
```

## ▶️ Cómo ejecutar el servidor

### Iniciar el servidor en modo desarrollo

```bash
uvicorn main:app --reload
```

El servidor estará disponible en: **http://127.0.0.1:8000**

### Acceder a la documentación interactiva

FastAPI genera automáticamente documentación interactiva:

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## 📚 Endpoints disponibles

### 🏠 Endpoint raíz

#### `GET /`
Devuelve información general de la API.

**Respuesta:**
```json
{
  "mensaje": "API de Tareas Persistente",
  "version": "3.0",
  "endpoints": {
    "tareas": "/tareas",
    "resumen": "/tareas/resumen",
    "completar_todas": "/tareas/completar_todas"
  }
}
```

---

### 📝 Gestión de tareas

#### `GET /tareas`
Obtiene todas las tareas con filtros opcionales.

**Query parameters:**
- `estado` (opcional): `pendiente`, `en_progreso`, `completada`
- `texto` (opcional): Busca en la descripción
- `prioridad` (opcional): `baja`, `media`, `alta`
- `orden` (opcional): `asc`, `desc` (ordena por fecha de creación)

**Ejemplos:**
```bash
# Obtener todas las tareas
GET http://127.0.0.1:8000/tareas

# Filtrar por estado
GET http://127.0.0.1:8000/tareas?estado=pendiente

# Buscar por texto
GET http://127.0.0.1:8000/tareas?texto=comprar

# Filtrar por prioridad
GET http://127.0.0.1:8000/tareas?prioridad=alta

# Ordenar por fecha descendente
GET http://127.0.0.1:8000/tareas?orden=desc

# Combinar filtros
GET http://127.0.0.1:8000/tareas?estado=pendiente&prioridad=alta&orden=asc
```

**Respuesta:**
```json
[
  {
    "id": 1,
    "descripcion": "Comprar leche",
    "estado": "pendiente",
    "prioridad": "alta",
    "fecha_creacion": "2025-10-17T10:30:00"
  }
]
```

---

#### `POST /tareas`
Crea una nueva tarea.

**Body (JSON):**
```json
{
  "descripcion": "Estudiar FastAPI",
  "estado": "pendiente",
  "prioridad": "media"
}
```

**Notas:**
- `descripcion`: Obligatorio, no puede estar vacío
- `estado`: Opcional (por defecto: `pendiente`)
- `prioridad`: Opcional (por defecto: `media`)

**Respuesta (201):**
```json
{
  "id": 1,
  "descripcion": "Estudiar FastAPI",
  "estado": "pendiente",
  "prioridad": "media",
  "fecha_creacion": "2025-10-17T10:30:00"
}
```

---

#### `PUT /tareas/{id}`
Actualiza una tarea existente.

**Body (JSON):**
```json
{
  "descripcion": "Estudiar FastAPI y SQLite",
  "estado": "en_progreso",
  "prioridad": "alta"
}
```

**Nota:** Todos los campos son opcionales. Solo se actualizarán los campos enviados.

**Respuesta (200):**
```json
{
  "id": 1,
  "descripcion": "Estudiar FastAPI y SQLite",
  "estado": "en_progreso",
  "prioridad": "alta",
  "fecha_creacion": "2025-10-17T10:30:00"
}
```

**Error (404):**
```json
{
  "detail": {
    "error": "Tarea no encontrada"
  }
}
```

---

#### `DELETE /tareas/{id}`
Elimina una tarea.

**Respuesta (200):**
```json
{
  "mensaje": "Tarea eliminada correctamente"
}
```

**Error (404):**
```json
{
  "detail": {
    "error": "Tarea no encontrada"
  }
}
```

---

### 📊 Endpoints especiales

#### `GET /tareas/resumen`
Devuelve un resumen estadístico de todas las tareas.

**Respuesta:**
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
    "media": 5,
    "alta": 3
  }
}
```

---

#### `PUT /tareas/completar_todas`
Marca todas las tareas como completadas.

**Respuesta:**
```json
{
  "mensaje": "Todas las tareas fueron marcadas como completadas"
}
```

**Respuesta (sin tareas):**
```json
{
  "mensaje": "No hay tareas para completar"
}
```

---

## 🧪 Ejecutar tests

```bash
# Ejecutar todos los tests
pytest test_TP3.py -v

# Ejecutar un test específico
pytest test_TP3.py::test_crear_tarea_exitosamente -v
```

## 🗄️ Base de datos

El proyecto utiliza SQLite con el archivo `tareas.db` que se crea automáticamente al iniciar la aplicación.

### Estructura de la tabla `tareas`

| Campo           | Tipo    | Descripción                          |
|-----------------|---------|--------------------------------------|
| id              | INTEGER | Clave primaria (autoincremental)     |
| descripcion     | TEXT    | Descripción de la tarea              |
| estado          | TEXT    | Estado: pendiente/en_progreso/completada |
| prioridad       | TEXT    | Prioridad: baja/media/alta           |
| fecha_creacion  | TEXT    | Fecha y hora de creación (ISO 8601)  |

### Verificar persistencia

1. Crear algunas tareas usando la API
2. Detener el servidor (Ctrl + C)
3. Volver a iniciar el servidor
4. Verificar que las tareas siguen disponibles

## 🛠️ Tecnologías utilizadas

- **FastAPI**: Framework web moderno para Python
- **Pydantic**: Validación de datos
- **SQLite**: Base de datos relacional ligera
- **Uvicorn**: Servidor ASGI de alto rendimiento

## 📁 Estructura del proyecto

```
TP3/
│
├── main.py           # Código principal de la API
├── tareas.db         # Base de datos SQLite (se genera automáticamente)
├── test_TP3.py       # Tests del proyecto
└── README.md         # Este archivo
```

## ⚠️ Manejo de errores

La API devuelve los siguientes códigos de estado:

- **200**: Operación exitosa
- **201**: Recurso creado exitosamente
- **400**: Error de validación (estado o prioridad inválidos)
- **404**: Recurso no encontrado
- **422**: Error de validación de datos (Pydantic)

## 📝 Ejemplos con cURL

### Crear una tarea
```bash
curl -X POST "http://127.0.0.1:8000/tareas" \
  -H "Content-Type: application/json" \
  -d '{
    "descripcion": "Hacer ejercicio",
    "estado": "pendiente",
    "prioridad": "alta"
  }'
```

### Obtener todas las tareas
```bash
curl "http://127.0.0.1:8000/tareas"
```

### Actualizar una tarea
```bash
curl -X PUT "http://127.0.0.1:8000/tareas/1" \
  -H "Content-Type: application/json" \
  -d '{
    "estado": "completada"
  }'
```

### Eliminar una tarea
```bash
curl -X DELETE "http://127.0.0.1:8000/tareas/1"
```

### Obtener resumen
```bash
curl "http://127.0.0.1:8000/tareas/resumen"
```
