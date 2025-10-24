# API de Gestión de Proyectos y Tareas

API REST completa para gestionar proyectos y tareas con relaciones 1:N, desarrollada con FastAPI y SQLite.

## 📋 Tabla de Contenidos

- [Características](#características)
- [Arquitectura](#arquitectura)
- [Instalación](#instalación)
- [Estructura de la Base de Datos](#estructura-de-la-base-de-datos)
- [Modelos de Datos](#modelos-de-datos)
- [Endpoints](#endpoints)
- [Ejemplos de Uso](#ejemplos-de-uso)
- [Testing](#testing)
- [Manejo de Errores](#manejo-de-errores)

## 🚀 Características

- **CRUD completo** para proyectos y tareas
- **Relaciones 1:N** con integridad referencial (CASCADE DELETE)
- **Filtros avanzados** por estado, prioridad, nombre y proyecto
- **Ordenamiento** ascendente/descendente por fecha de creación
- **Estadísticas y resúmenes** por proyecto y globales
- **Validación robusta** con Pydantic
- **Manejo de errores** HTTP estandarizado
- **Testing completo** con pytest (60+ tests)

## 🏗️ Arquitectura

### Estructura de Archivos

```
proyecto/
├── main.py              # Aplicación FastAPI y endpoints
├── database.py          # Capa de acceso a datos (SQLite)
├── models.py            # Modelos Pydantic para validación
├── conftest.py          # Configuración de fixtures para pytest
├── test_TP4.py          # Suite de tests completa
├── requirements.txt     # Dependencias del proyecto
└── tareas.db           # Base de datos SQLite (generada automáticamente)
```

### Stack Tecnológico

- **FastAPI 0.104.1**: Framework web moderno y rápido
- **SQLite 3**: Base de datos relacional embebida
- **Pydantic 2.7.4+**: Validación de datos con type hints
- **Pytest 7.4.3**: Framework de testing
- **Uvicorn 0.24.0**: Servidor ASGI de alto rendimiento

## 💾 Estructura de la Base de Datos

### Tabla: `proyectos`

| Campo          | Tipo    | Restricciones                    |
|----------------|---------|----------------------------------|
| id             | INTEGER | PRIMARY KEY AUTOINCREMENT        |
| nombre         | TEXT    | NOT NULL UNIQUE                  |
| descripcion    | TEXT    | NULL                             |
| fecha_creacion | TEXT    | NOT NULL (ISO 8601 UTC)          |

### Tabla: `tareas`

| Campo          | Tipo    | Restricciones                          |
|----------------|---------|----------------------------------------|
| id             | INTEGER | PRIMARY KEY AUTOINCREMENT              |
| descripcion    | TEXT    | NOT NULL                               |
| estado         | TEXT    | NOT NULL (enum)                        |
| prioridad      | TEXT    | NOT NULL (enum)                        |
| proyecto_id    | INTEGER | NOT NULL, FOREIGN KEY → proyectos(id) |
| fecha_creacion | TEXT    | NOT NULL (ISO 8601 UTC)                |

**Integridad Referencial:**
- `ON DELETE CASCADE`: Al eliminar un proyecto, se eliminan automáticamente todas sus tareas
- `PRAGMA foreign_keys=ON`: Activado en todas las conexiones

### Configuración SQLite

```sql
PRAGMA journal_mode=WAL;      -- Write-Ahead Logging (producción)
PRAGMA synchronous=NORMAL;    -- Balance rendimiento/seguridad
PRAGMA foreign_keys=ON;       -- Integridad referencial activa
```

En modo de testing:
```sql
PRAGMA journal_mode=DELETE;   -- Evita archivos -wal/-shm en Windows
PRAGMA synchronous=OFF;       -- Mayor velocidad en tests
```

## 📦 Modelos de Datos

### Proyectos

#### `ProyectoCreate` (Request)
```python
{
  "nombre": str,              # min_length=1, se hace trim
  "descripcion": str | null   # opcional
}
```

#### `ProyectoUpdate` (Request)
```python
{
  "nombre": str | null,       # opcional, min_length=1 si presente
  "descripcion": str | null   # opcional
}
```

#### `Proyecto` (Response)
```python
{
  "id": int,
  "nombre": str,
  "descripcion": str | null,
  "fecha_creacion": str,      # ISO 8601 UTC
  "total_tareas": int         # contador de tareas asociadas
}
```

### Tareas

#### `TareaCreate` (Request)
```python
{
  "descripcion": str,         # min_length=1, se hace trim
  "estado": "pendiente" | "en_progreso" | "completada",  # default: "pendiente"
  "prioridad": "baja" | "media" | "alta"                 # default: "media"
}
```

#### `TareaUpdate` (Request)
```python
{
  "descripcion": str | null,
  "estado": "pendiente" | "en_progreso" | "completada" | null,
  "prioridad": "baja" | "media" | "alta" | null,
  "proyecto_id": int | null   # permite mover tarea a otro proyecto
}
```

#### `Tarea` (Response)
```python
{
  "id": int,
  "descripcion": str,
  "estado": str,
  "prioridad": str,
  "proyecto_id": int,
  "fecha_creacion": str,      # ISO 8601 UTC
  "proyecto_nombre": str      # JOIN con tabla proyectos
}
```

## 🔌 Endpoints

### Información General

#### `GET /`
Información de la API y lista de endpoints disponibles.

**Response:** `200 OK`
```json
{
  "nombre": "API de Gestión de Proyectos y Tareas",
  "version": "2.0.0",
  "descripcion": "...",
  "endpoints": { ... }
}
```

---

### Proyectos

#### `GET /proyectos`
Lista todos los proyectos con contador de tareas.

**Query Parameters:**
- `nombre` (opcional): Filtro parcial por nombre (LIKE %nombre%)

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "nombre": "Proyecto Web",
    "descripcion": "Desarrollo del sitio",
    "fecha_creacion": "2025-01-15T10:30:00.000000+00:00",
    "total_tareas": 5
  }
]
```

---

#### `GET /proyectos/{proyecto_id}`
Obtiene un proyecto específico con contador de tareas.

**Response:** `200 OK` (mismo formato que arriba)

**Errores:**
- `404 NOT FOUND`: Proyecto no encontrado

---

#### `POST /proyectos`
Crea un nuevo proyecto.

**Request Body:**
```json
{
  "nombre": "Nuevo Proyecto",
  "descripcion": "Descripción opcional"
}
```

**Response:** `201 CREATED`
```json
{
  "id": 2,
  "nombre": "Nuevo Proyecto",
  "descripcion": "Descripción opcional",
  "fecha_creacion": "2025-01-15T11:00:00.000000+00:00",
  "total_tareas": 0
}
```

**Errores:**
- `409 CONFLICT`: Ya existe un proyecto con ese nombre
- `422 UNPROCESSABLE ENTITY`: Validación fallida (nombre vacío)

---

#### `PUT /proyectos/{proyecto_id}`
Actualiza un proyecto existente.

**Request Body:**
```json
{
  "nombre": "Proyecto Actualizado",
  "descripcion": "Nueva descripción"
}
```

**Response:** `200 OK` (formato Proyecto)

**Errores:**
- `404 NOT FOUND`: Proyecto no encontrado
- `422 UNPROCESSABLE ENTITY`: Validación fallida

---

#### `DELETE /proyectos/{proyecto_id}`
Elimina un proyecto y todas sus tareas (CASCADE).

**Response:** `200 OK`
```json
{
  "mensaje": "Proyecto y sus tareas eliminados correctamente",
  "tareas_eliminadas": 3
}
```

**Errores:**
- `404 NOT FOUND`: Proyecto no encontrado

---

### Tareas

#### `GET /proyectos/{proyecto_id}/tareas`
Lista tareas de un proyecto específico.

**Query Parameters:**
- `estado` (opcional): "pendiente" | "en_progreso" | "completada"
- `prioridad` (opcional): "baja" | "media" | "alta"
- `orden` (opcional): "asc" | "desc" (por fecha_creacion)

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "descripcion": "Implementar login",
    "estado": "en_progreso",
    "prioridad": "alta",
    "proyecto_id": 1,
    "fecha_creacion": "2025-01-15T10:45:00.000000+00:00",
    "proyecto_nombre": "Proyecto Web"
  }
]
```

**Errores:**
- `404 NOT FOUND`: Proyecto no encontrado
- `400 BAD REQUEST`: Filtros inválidos

---

#### `POST /proyectos/{proyecto_id}/tareas`
Crea una tarea en un proyecto.

**Request Body:**
```json
{
  "descripcion": "Nueva tarea",
  "estado": "pendiente",
  "prioridad": "media"
}
```

**Response:** `201 CREATED` (formato Tarea)

**Errores:**
- `400 BAD REQUEST`: Proyecto no encontrado
- `422 UNPROCESSABLE ENTITY`: Validación fallida

---

#### `GET /tareas`
Lista todas las tareas de todos los proyectos.

**Query Parameters:**
- `proyecto_id` (opcional): Filtrar por proyecto
- `estado` (opcional): Filtrar por estado
- `prioridad` (opcional): Filtrar por prioridad
- `orden` (opcional): Ordenar por fecha

**Response:** `200 OK` (array de Tarea)

---

#### `GET /tareas/{tarea_id}`
Obtiene una tarea específica.

**Response:** `200 OK` (formato Tarea)

**Errores:**
- `404 NOT FOUND`: Tarea no encontrada

---

#### `PUT /tareas/{tarea_id}`
Actualiza una tarea (puede moverla a otro proyecto).

**Request Body:**
```json
{
  "descripcion": "Tarea actualizada",
  "estado": "completada",
  "prioridad": "alta",
  "proyecto_id": 2
}
```

**Response:** `200 OK` (formato Tarea)

**Errores:**
- `404 NOT FOUND`: Tarea o proyecto no encontrado
- `422 UNPROCESSABLE ENTITY`: Validación fallida

---

#### `DELETE /tareas/{tarea_id}`
Elimina una tarea.

**Response:** `200 OK`
```json
{
  "mensaje": "Tarea eliminada correctamente"
}
```

**Errores:**
- `404 NOT FOUND`: Tarea no encontrada

---

### Estadísticas

#### `GET /proyectos/{proyecto_id}/resumen`
Obtiene estadísticas de un proyecto.

**Response:** `200 OK`
```json
{
  "proyecto_id": 1,
  "proyecto_nombre": "Proyecto Web",
  "total_tareas": 10,
  "por_estado": {
    "pendiente": 3,
    "en_progreso": 4,
    "completada": 3
  },
  "por_prioridad": {
    "baja": 2,
    "media": 5,
    "alta": 3
  }
}
```

**Errores:**
- `404 NOT FOUND`: Proyecto no encontrado

---

#### `GET /resumen`
Resumen general de toda la aplicación.

**Response:** `200 OK`
```json
{
  "total_proyectos": 5,
  "total_tareas": 25,
  "tareas_por_estado": {
    "pendiente": 8,
    "en_progreso": 10,
    "completada": 7
  },
  "proyecto_con_mas_tareas": {
    "id": 1,
    "nombre": "Proyecto Web",
    "cantidad_tareas": 10
  }
}
```

**Nota:** `proyecto_con_mas_tareas` es `null` si no hay proyectos con tareas.

---

## 💡 Ejemplos de Uso

### Flujo Completo con cURL

```bash
# 1. Crear proyecto
curl -X POST http://localhost:8000/proyectos \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Mi Proyecto", "descripcion": "Desarrollo web"}'

# Response: {"id": 1, "nombre": "Mi Proyecto", ...}

# 2. Crear tareas
curl -X POST http://localhost:8000/proyectos/1/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Diseñar base de datos", "prioridad": "alta"}'

curl -X POST http://localhost:8000/proyectos/1/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Implementar API", "estado": "en_progreso"}'

# 3. Listar tareas del proyecto
curl http://localhost:8000/proyectos/1/tareas

# 4. Filtrar tareas completadas de alta prioridad
curl "http://localhost:8000/tareas?estado=completada&prioridad=alta"

# 5. Actualizar tarea (cambiar estado)
curl -X PUT http://localhost:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{"estado": "completada"}'

# 6. Mover tarea a otro proyecto
curl -X PUT http://localhost:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{"proyecto_id": 2}'

# 7. Obtener estadísticas del proyecto
curl http://localhost:8000/proyectos/1/resumen

# 8. Obtener resumen general
curl http://localhost:8000/resumen

# 9. Eliminar proyecto (elimina tareas en cascade)
curl -X DELETE http://localhost:8000/proyectos/1
```

### Ejemplo con Python Requests

```python
import requests

BASE_URL = "http://localhost:8000"

# Crear proyecto
response = requests.post(f"{BASE_URL}/proyectos", json={
    "nombre": "Proyecto Python",
    "descripcion": "Automatización de tareas"
})
proyecto = response.json()
proyecto_id = proyecto["id"]

# Crear múltiples tareas
tareas = [
    {"descripcion": "Setup entorno", "prioridad": "alta"},
    {"descripcion": "Escribir scripts", "estado": "en_progreso"},
    {"descripcion": "Documentar código", "prioridad": "baja"}
]

for tarea in tareas:
    requests.post(f"{BASE_URL}/proyectos/{proyecto_id}/tareas", json=tarea)

# Listar tareas pendientes
response = requests.get(f"{BASE_URL}/tareas", params={"estado": "pendiente"})
print(response.json())

# Obtener estadísticas
response = requests.get(f"{BASE_URL}/proyectos/{proyecto_id}/resumen")
print(response.json())
```

---

## 🧪 Testing

### Ejecutar Tests

```bash
# Todos los tests
pytest test_TP4.py -v

# Tests específicos por categoría
pytest test_TP4.py -k "test_2" -v  # Solo CRUD de proyectos
pytest test_TP4.py -k "test_4" -v  # Solo filtros avanzados

# Con coverage
pytest test_TP4.py --cov=. --cov-report=html
```

### Estructura de Tests

La suite incluye **60+ tests** organizados en 9 categorías:

1. **Diseño de BD Relacional** (2 tests)
   - Verificación de tablas y columnas
   - Validación de claves foráneas

2. **CRUD de Proyectos** (6 tests)
   - Crear, listar, obtener, actualizar, eliminar
   - Manejo de nombres duplicados

3. **Tareas Asociadas a Proyectos** (6 tests)
   - Creación en proyectos existentes/inexistentes
   - Listado por proyecto
   - Mover tareas entre proyectos

4. **Filtros y Búsquedas Avanzadas** (6 tests)
   - Filtros por nombre, estado, prioridad
   - Combinación de múltiples filtros
   - Ordenamiento ascendente/descendente

5. **Resúmenes y Estadísticas** (4 tests)
   - Resumen por proyecto
   - Resumen general
   - Manejo de casos vacíos

6. **Validación con Pydantic** (4 tests)
   - Campos vacíos
   - Estados y prioridades inválidos

7. **Manejo de Errores** (4 tests)
   - Códigos HTTP correctos (404, 400, 409, 422)

8. **Integridad Referencial** (4 tests)
   - CASCADE DELETE
   - Validación de claves foráneas
   - Movimiento de tareas

9. **Tests Adicionales** (2 tests)
   - Listado global de tareas
   - Filtros combinados avanzados

---

## ⚠️ Manejo de Errores

### Códigos de Estado HTTP

| Código | Significado | Casos de Uso |
|--------|-------------|--------------|
| `200 OK` | Éxito en GET, PUT, DELETE | Operaciones exitosas |
| `201 CREATED` | Recurso creado | POST exitoso |
| `400 BAD REQUEST` | Solicitud inválida | Proyecto inexistente al crear tarea, filtros inválidos |
| `404 NOT FOUND` | Recurso no encontrado | GET/PUT/DELETE de ID inexistente |
| `409 CONFLICT` | Conflicto de estado | Nombre de proyecto duplicado |
| `422 UNPROCESSABLE ENTITY` | Validación fallida | Datos inválidos en Pydantic |

### Formato de Errores

Todos los errores siguen el formato estándar de FastAPI:

```json
{
  "detail": {
    "error": "Descripción del error"
  }
}
```

O para errores de validación (422):

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "nombre"],
      "msg": "String should have at least 1 character",
      "input": "",
      "ctx": {"min_length": 1}
    }
  ]
}
```

---

## 🔒 Consideraciones de Seguridad

- **Validación de entrada**: Pydantic valida todos los datos de entrada
- **SQL Injection**: Prevención mediante queries parametrizadas
- **Integridad referencial**: Activada con `PRAGMA foreign_keys=ON`
- **Timeouts de conexión**: 30 segundos para evitar bloqueos
- **Manejo de concurrencia**: WAL mode en producción

---

## 📝 Notas Técnicas

### Gestión de Conexiones

```python
# Patrón utilizado en database.py
with closing(get_connection()) as conn:
    cursor = conn.cursor()
    # ... operaciones ...
    conn.commit()
```

Este patrón garantiza que las conexiones se cierren correctamente, especialmente importante en Windows.

### Formato de Fechas

Todas las fechas se almacenan en formato ISO 8601 con timezone UTC:

```python
datetime.now(timezone.utc).isoformat()
# Ejemplo: "2025-01-15T10:30:00.000000+00:00"
```

### Modo de Testing

El sistema detecta automáticamente si está ejecutándose bajo pytest:

```python
_RUNNING_PYTEST = any('pytest' in str(arg) for arg in sys.argv)
```

Esto permite:
- Base de datos temporal por proceso
- Modo DELETE en lugar de WAL
- Inicialización explícita de BD en tests

---

## 📚 Referencias

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [SQLite Foreign Keys](https://www.sqlite.org/foreignkeys.html)
- [pytest Documentation](https://docs.pytest.org/)

---

## 📄 Licencia

Este proyecto es código educativo desarrollado para fines académicos.

---

## 👥 Contribuciones

Para contribuir al proyecto:

1. Asegúrate de que todos los tests pasen: `pytest test_TP4.py -v`
2. Mantén la cobertura de tests por encima del 90%
3. Sigue los estándares de código PEP 8
4. Documenta nuevos endpoints en este README