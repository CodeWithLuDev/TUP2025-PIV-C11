# TP3 - API de Tareas Persistente con SQLite

## 📋 Descripción

API REST desarrollada con FastAPI que implementa un CRUD completo de tareas con persistencia en base de datos SQLite. Los datos se mantienen almacenados incluso después de reiniciar el servidor.

## 🚀 Instalación y Ejecución

### 1. Instalar dependencias

```bash
pip install fastapi uvicorn sqlite3 pydantic pytest httpx
```

### 2. Iniciar el servidor

```bash
uvicorn main:app --reload
```

El servidor se iniciará en: `http://localhost:8000`

### 3. Acceder a la documentación interactiva

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🗄️ Base de Datos

El archivo `tareas.db` se crea automáticamente al iniciar la aplicación por primera vez.

### Estructura de la tabla `tareas`:

| Campo           | Tipo    | Descripción                    |
|-----------------|---------|--------------------------------|
| id              | INTEGER | Clave primaria auto incremental|
| descripcion     | TEXT    | Descripción de la tarea        |
| estado          | TEXT    | Estado: pendiente/en_progreso/completada |
| prioridad       | TEXT    | Prioridad: baja/media/alta     |
| fecha_creacion  | TEXT    | Fecha y hora de creación (ISO) |

## 📡 Endpoints

### 1. **GET /** - Información de la API

```bash
curl http://localhost:8000/
```

### 2. **GET /tareas** - Listar todas las tareas

```bash
# Todas las tareas
curl http://localhost:8000/tareas

# Filtrar por estado
curl http://localhost:8000/tareas?estado=pendiente

# Buscar por texto
curl http://localhost:8000/tareas?texto=comprar

# Filtrar por prioridad
curl http://localhost:8000/tareas?prioridad=alta

# Ordenar por fecha (ascendente o descendente)
curl http://localhost:8000/tareas?orden=desc

# Combinar filtros
curl "http://localhost:8000/tareas?estado=pendiente&prioridad=alta&orden=asc"
```

**Respuesta:**
```json
[
  {
    "id": 1,
    "descripcion": "Comprar leche",
    "estado": "pendiente",
    "prioridad": "media",
    "fecha_creacion": "2025-10-16T20:30:00.123456"
  }
]
```

### 3. **POST /tareas** - Crear una tarea

```bash
curl -X POST http://localhost:8000/tareas \
  -H "Content-Type: application/json" \
  -d '{
    "descripcion": "Estudiar FastAPI",
    "estado": "pendiente",
    "prioridad": "alta"
  }'
```

**Respuesta (201):**
```json
{
  "id": 1,
  "descripcion": "Estudiar FastAPI",
  "estado": "pendiente",
  "prioridad": "alta",
  "fecha_creacion": "2025-10-16T20:30:00.123456"
}
```

### 4. **PUT /tareas/{id}** - Actualizar una tarea

```bash
curl -X PUT http://localhost:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{
    "estado": "completada",
    "prioridad": "baja"
  }'
```

**Respuesta (200):**
```json
{
  "id": 1,
  "descripcion": "Estudiar FastAPI",
  "estado": "completada",
  "prioridad": "baja",
  "fecha_creacion": "2025-10-16T20:30:00.123456"
}
```

### 5. **DELETE /tareas/{id}** - Eliminar una tarea

```bash
curl -X DELETE http://localhost:8000/tareas/1
```

**Respuesta (200):**
```json
{
  "mensaje": "Tarea eliminada exitosamente"
}
```

### 6. **GET /tareas/resumen** - Resumen de tareas

```bash
curl http://localhost:8000/tareas/resumen
```

**Respuesta:**
```json
{
  "pendiente": 5,
  "en_progreso": 2,
  "completada": 8,
  "por_prioridad": {
    "baja": 3,
    "media": 7,
    "alta": 5
  }
}
```

### 7. **PUT /tareas/completar_todas** - Completar todas las tareas

```bash
curl -X PUT http://localhost:8000/tareas/completar_todas
```

**Respuesta:**
```json
{
  "mensaje": "Todas las tareas han sido marcadas como completadas",
  "tareas_actualizadas": 7
}
```

## ✅ Validaciones

- **Descripción**: No puede estar vacía
- **Estado**: Solo acepta: `pendiente`, `en_progreso`, `completada`
- **Prioridad**: Solo acepta: `baja`, `media`, `alta`
- **Errores HTTP**:
  - 400: Validación fallida
  - 404: Tarea no encontrada
  - 422: Datos no procesables

## 🧪 Ejecutar Tests

```bash
# Todos los tests
pytest test_TP3.py -v

# Un test específico
pytest test_TP3.py::test_00_nombre_del_test -v
```

## 📦 Estructura del Proyecto

```
TP3/
├── main.py           # Código principal de la API
├── tareas.db         # Base de datos SQLite (generada automáticamente)
├── test_TP3.py       # Tests del proyecto
└── README.md         # Este archivo
```

## 🔧 Tecnologías Utilizadas

- **FastAPI**: Framework web moderno y rápido
- **SQLite**: Base de datos SQL ligera y sin servidor
- **Pydantic**: Validación de datos
- **Uvicorn**: Servidor ASGI
- **Pytest**: Framework de testing

## 👨‍💻 Autor

**Gonzalo Moreno** - Alumno 62490  
UTN FRT - Programación IV - 2025

## 📅 Fecha de Entrega

17 de Octubre de 2025 - 21:00hs

## 🎯 Características Implementadas

- ✅ Persistencia con SQLite
- ✅ CRUD completo de tareas
- ✅ Filtros por estado, texto y prioridad
- ✅ Ordenamiento por fecha
- ✅ Validaciones con Pydantic
- ✅ Manejo de errores HTTP
- ✅ Resumen de tareas por estado y prioridad
- ✅ Endpoint para completar todas las tareas
- ✅ Documentación automática con Swagger
- ✅ Context manager para manejo seguro de BD