# TP4 - API de Gestión de Proyectos y Tareas

Sistema de gestión de proyectos y tareas con relaciones entre tablas usando FastAPI y SQLite.

## 📋 Características

- ✅ CRUD completo de proyectos y tareas
- ✅ Relaciones 1:N entre proyectos y tareas
- ✅ Integridad referencial con claves foráneas
- ✅ CASCADE DELETE automático
- ✅ Filtros avanzados y combinables
- ✅ Estadísticas y resúmenes
- ✅ Validación con Pydantic
- ✅ Manejo robusto de errores

## 🗂️ Estructura de la Base de Datos

### Tabla `proyectos`
```sql
id              INTEGER PRIMARY KEY AUTOINCREMENT
nombre          TEXT NOT NULL UNIQUE
descripcion     TEXT
fecha_creacion  TEXT NOT NULL
```

### Tabla `tareas`
```sql
id              INTEGER PRIMARY KEY AUTOINCREMENT
descripcion     TEXT NOT NULL
estado          TEXT NOT NULL CHECK(estado IN ('pendiente', 'en_progreso', 'completada'))
prioridad       TEXT NOT NULL CHECK(prioridad IN ('baja', 'media', 'alta'))
proyecto_id     INTEGER NOT NULL
fecha_creacion  TEXT NOT NULL
FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
```

### Relación entre tablas
```
proyectos (1) ──< (N) tareas
```

- Un proyecto puede tener múltiples tareas
- Una tarea pertenece a un solo proyecto
- Al eliminar un proyecto, se eliminan automáticamente sus tareas (CASCADE)

## 🚀 Instalación y Ejecución

### Requisitos
```bash
pip install fastapi uvicorn pydantic sqlite3
```

### Ejecutar el servidor
```bash
uvicorn main:app --reload
```

El servidor estará disponible en: `http://localhost:8000`

### Ejecutar tests
```bash
pytest test_TP4.py -v
```

## 📚 Documentación de la API

### Acceder a la documentación interactiva
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔗 Endpoints

### Proyectos

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/proyectos` | Lista todos los proyectos |
| `GET` | `/proyectos/{id}` | Obtiene un proyecto específico |
| `POST` | `/proyectos` | Crea un nuevo proyecto |
| `PUT` | `/proyectos/{id}` | Actualiza un proyecto |
| `DELETE` | `/proyectos/{id}` | Elimina un proyecto y sus tareas |

### Tareas

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/tareas` | Lista todas las tareas |
| `GET` | `/proyectos/{id}/tareas` | Lista tareas de un proyecto |
| `POST` | `/proyectos/{id}/tareas` | Crea una tarea en un proyecto |
| `PUT` | `/tareas/{id}` | Actualiza una tarea |
| `DELETE` | `/tareas/{id}` | Elimina una tarea |

### Estadísticas

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/proyectos/{id}/resumen` | Estadísticas de un proyecto |
| `GET` | `/resumen` | Resumen general de la aplicación |

## 📝 Ejemplos de Uso

### Crear un proyecto
```bash
curl -X POST "http://localhost:8000/proyectos" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Proyecto Alpha",
    "descripcion": "Sistema de gestión empresarial"
  }'
```

**Respuesta:**
```json
{
  "id": 1,
  "nombre": "Proyecto Alpha",
  "descripcion": "Sistema de gestión empresarial",
  "fecha_creacion": "2025-10-24T15:30:00",
  "total_tareas": 0
}
```

### Listar proyectos con filtro
```bash
curl "http://localhost:8000/proyectos?nombre=Alpha"
```

### Crear una tarea
```bash
curl -X POST "http://localhost:8000/proyectos/1/tareas" \
  -H "Content-Type: application/json" \
  -d '{
    "descripcion": "Implementar autenticación",
    "estado": "en_progreso",
    "prioridad": "alta"
  }'
```

**Respuesta:**
```json
{
  "id": 1,
  "descripcion": "Implementar autenticación",
  "estado": "en_progreso",
  "prioridad": "alta",
  "proyecto_id": 1,
  "fecha_creacion": "2025-10-24T15:35:00"
}
```

### Filtrar tareas con múltiples criterios
```bash
curl "http://localhost:8000/tareas?estado=completada&prioridad=alta&orden=desc"
```

### Mover una tarea a otro proyecto
```bash
curl -X PUT "http://localhost:8000/tareas/1" \
  -H "Content-Type: application/json" \
  -d '{
    "proyecto_id": 2
  }'
```

### Obtener resumen de un proyecto
```bash
curl "http://localhost:8000/proyectos/1/resumen"
```

**Respuesta:**
```json
{
  "proyecto_id": 1,
  "proyecto_nombre": "Proyecto Alpha",
  "total_tareas": 15,
  "por_estado": {
    "pendiente": 5,
    "en_progreso": 7,
    "completada": 3
  },
  "por_prioridad": {
    "baja": 4,
    "media": 8,
    "alta": 3
  }
}
```

### Obtener resumen general
```bash
curl "http://localhost:8000/resumen"
```

**Respuesta:**
```json
{
  "total_proyectos": 3,
  "total_tareas": 42,
  "tareas_por_estado": {
    "pendiente": 15,
    "en_progreso": 20,
    "completada": 7
  },
  "proyecto_con_mas_tareas": {
    "id": 1,
    "nombre": "Proyecto Alpha",
    "cantidad_tareas": 15
  }
}
```

## 🔍 Filtros Disponibles

### Proyectos
- `nombre`: Búsqueda parcial por nombre

### Tareas
- `estado`: `pendiente`, `en_progreso`, `completada`
- `prioridad`: `baja`, `media`, `alta`
- `proyecto_id`: ID del proyecto
- `orden`: `asc` (ascendente) o `desc` (descendente) por fecha

**Ejemplo de filtros combinados:**
```bash
curl "http://localhost:8000/tareas?estado=pendiente&prioridad=alta&proyecto_id=1&orden=desc"
```

## ⚠️ Manejo de Errores

La API devuelve códigos HTTP apropiados:

- `200`: Operación exitosa
- `201`: Recurso creado
- `400`: Datos inválidos
- `404`: Recurso no encontrado
- `409`: Conflicto (ej: nombre duplicado)

**Ejemplo de error:**
```json
{
  "detail": "Ya existe un proyecto con el nombre 'Proyecto Alpha'"
}
```

## 🧪 Pruebas de Integridad Referencial

### Escenario 1: Crear proyecto y tareas
```bash
# 1. Crear proyecto
curl -X POST "http://localhost:8000/proyectos" -d '{"nombre":"Test"}'

# 2. Crear tareas
curl -X POST "http://localhost:8000/proyectos/1/tareas" -d '{"descripcion":"Tarea 1"}'
curl -X POST "http://localhost:8000/proyectos/1/tareas" -d '{"descripcion":"Tarea 2"}'
```

### Escenario 2: Eliminar proyecto (CASCADE)
```bash
# Elimina el proyecto y automáticamente sus 2 tareas
curl -X DELETE "http://localhost:8000/proyectos/1"
```

### Escenario 3: Intentar crear tarea en proyecto inexistente
```bash
# Esto fallará con error 400
curl -X POST "http://localhost:8000/proyectos/999/tareas" -d '{"descripcion":"Tarea"}'
```

## 📁 Archivos del Proyecto
```
TP4/
├── main.py          # API principal con todos los endpoints
├── models.py        # Modelos Pydantic para validación
├── database.py      # Funciones de acceso a la base de datos
├── test_TP4.py      # Suite de tests automatizados
├── tareas.db        # Base de datos SQLite (se crea automáticamente)
└── README.md        # Este archivo
```

## 👨‍💻 Autor

[Tu nombre]

## 📅 Fecha de Entrega

24 de Octubre de 2025