# TP4 - API de Gestión de Proyectos y Tareas

API RESTful construida con FastAPI que implementa un sistema de gestión de proyectos y tareas con relaciones 1:N (uno a muchos).

## 📋 Requisitos

- Python 3.8+
- FastAPI
- Uvicorn
- Pydantic
- SQLite3

## 🚀 Instalación y Ejecución

### Instalar dependencias

```bash
pip install fastapi uvicorn
```

### Iniciar el servidor

```bash
uvicorn main:app --reload
```

El servidor estará disponible en: `http://localhost:8000`

### Documentación interactiva

Una vez iniciado el servidor, puedes acceder a:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🗄️ Estructura de la Base de Datos

### Diagrama de Relaciones

```
┌─────────────────────────┐
│      PROYECTOS          │
├─────────────────────────┤
│ id (PK)                 │
│ nombre (UNIQUE)         │
│ descripcion             │
│ fecha_creacion          │
└───────────┬─────────────┘
            │
            │ 1:N
            │
┌───────────▼─────────────┐
│        TAREAS           │
├─────────────────────────┤
│ id (PK)                 │
│ descripcion             │
│ estado                  │
│ prioridad               │
│ proyecto_id (FK)        │
│ fecha_creacion          │
└─────────────────────────┘
```

### Tabla: proyectos

| Campo           | Tipo    | Restricciones           |
|-----------------|---------|-------------------------|
| id              | INTEGER | PRIMARY KEY, AUTOINCREMENT |
| nombre          | TEXT    | NOT NULL, UNIQUE        |
| descripcion     | TEXT    | NULL                    |
| fecha_creacion  | TEXT    | NOT NULL                |

### Tabla: tareas

| Campo           | Tipo    | Restricciones                    |
|-----------------|---------|----------------------------------|
| id              | INTEGER | PRIMARY KEY, AUTOINCREMENT       |
| descripcion     | TEXT    | NOT NULL                         |
| estado          | TEXT    | NOT NULL                         |
| prioridad       | TEXT    | NOT NULL                         |
| proyecto_id     | INTEGER | FOREIGN KEY → proyectos(id), NOT NULL |
| fecha_creacion  | TEXT    | NOT NULL                         |

### Relación entre Tablas

La relación entre `proyectos` y `tareas` es **1:N** (uno a muchos):
- Un proyecto puede tener **muchas tareas**
- Cada tarea pertenece a **un solo proyecto**

**Integridad Referencial:**
- `proyecto_id` es una clave foránea que referencia a `proyectos.id`
- `ON DELETE CASCADE`: Al eliminar un proyecto, todas sus tareas asociadas se eliminan automáticamente
- No se puede crear una tarea con un `proyecto_id` que no exista

## 📡 Endpoints de la API

### Proyectos

#### Listar todos los proyectos

```bash
GET /proyectos
```

**Filtros opcionales:**
- `?nombre=texto` - Busca proyectos cuyo nombre contenga el texto

**Ejemplo:**
```bash
curl http://localhost:8000/proyectos
curl http://localhost:8000/proyectos?nombre=Web
```

**Respuesta:**
```json
[
  {
    "id": 1,
    "nombre": "Desarrollo Web",
    "descripcion": "Proyecto de desarrollo web",
    "fecha_creacion": "2025-10-20T10:30:00"
  }
]
```

#### Obtener un proyecto específico

```bash
GET /proyectos/{id}
```

**Ejemplo:**
```bash
curl http://localhost:8000/proyectos/1
```

**Respuesta:**
```json
{
  "id": 1,
  "nombre": "Desarrollo Web",
  "descripcion": "Proyecto de desarrollo web",
  "fecha_creacion": "2025-10-20T10:30:00",
  "total_tareas": 5
}
```

#### Crear un proyecto

```bash
POST /proyectos
```

**Body:**
```json
{
  "nombre": "Proyecto Alpha",
  "descripcion": "Descripción del proyecto"
}
```

**Ejemplo:**
```bash
curl -X POST http://localhost:8000/proyectos \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Proyecto Alpha",
    "descripcion": "Mi nuevo proyecto"
  }'
```

**Respuesta:** `201 Created`

#### Actualizar un proyecto

```bash
PUT /proyectos/{id}
```

**Body:**
```json
{
  "nombre": "Proyecto Modificado",
  "descripcion": "Nueva descripción"
}
```

**Ejemplo:**
```bash
curl -X PUT http://localhost:8000/proyectos/1 \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Proyecto Actualizado",
    "descripcion": "Descripción modificada"
  }'
```

#### Eliminar un proyecto

```bash
DELETE /proyectos/{id}
```

**Ejemplo:**
```bash
curl -X DELETE http://localhost:8000/proyectos/1
```

**Respuesta:**
```json
{
  "mensaje": "Proyecto eliminado",
  "tareas_eliminadas": 3
}
```

⚠️ **Importante:** Al eliminar un proyecto se eliminan automáticamente todas sus tareas (CASCADE).

### Tareas

#### Listar todas las tareas

```bash
GET /tareas
```

**Filtros opcionales:**
- `?estado=pendiente|en_progreso|completada`
- `?prioridad=baja|media|alta`
- `?proyecto_id=1`
- `?orden=asc|desc`

**Ejemplo:**
```bash
curl http://localhost:8000/tareas
curl http://localhost:8000/tareas?estado=completada&prioridad=alta
curl http://localhost:8000/tareas?proyecto_id=1&orden=desc
```

**Respuesta:**
```json
[
  {
    "id": 1,
    "descripcion": "Implementar autenticación",
    "estado": "en_progreso",
    "prioridad": "alta",
    "proyecto_id": 1,
    "fecha_creacion": "2025-10-20T11:00:00"
  }
]
```

#### Listar tareas de un proyecto

```bash
GET /proyectos/{id}/tareas
```

**Filtros opcionales:**
- `?estado=pendiente|en_progreso|completada`
- `?prioridad=baja|media|alta`
- `?orden=asc|desc`

**Ejemplo:**
```bash
curl http://localhost:8000/proyectos/1/tareas
curl http://localhost:8000/proyectos/1/tareas?estado=pendiente
```

#### Crear tarea en un proyecto

```bash
POST /proyectos/{id}/tareas
```

**Body:**
```json
{
  "descripcion": "Implementar login",
  "estado": "pendiente",
  "prioridad": "alta"
}
```

**Ejemplo:**
```bash
curl -X POST http://localhost:8000/proyectos/1/tareas \
  -H "Content-Type: application/json" \
  -d '{
    "descripcion": "Crear API endpoints",
    "estado": "pendiente",
    "prioridad": "alta"
  }'
```

**Valores por defecto:**
- `estado`: "pendiente"
- `prioridad`: "media"

**Respuesta:** `201 Created`

#### Actualizar una tarea

```bash
PUT /tareas/{id}
```

**Body:**
```json
{
  "descripcion": "Nueva descripción",
  "estado": "completada",
  "prioridad": "baja",
  "proyecto_id": 2
}
```

**Ejemplo:**
```bash
curl -X PUT http://localhost:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{
    "estado": "completada"
  }'
```

**Nota:** Puedes cambiar el `proyecto_id` para mover una tarea a otro proyecto.

#### Eliminar una tarea

```bash
DELETE /tareas/{id}
```

**Ejemplo:**
```bash
curl -X DELETE http://localhost:8000/tareas/1
```

### Resúmenes y Estadísticas

#### Resumen de un proyecto

```bash
GET /proyectos/{id}/resumen
```

**Ejemplo:**
```bash
curl http://localhost:8000/proyectos/1/resumen
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

#### Resumen general

```bash
GET /resumen
```

**Ejemplo:**
```bash
curl http://localhost:8000/resumen
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

## 🎯 Valores Válidos

### Estados de Tareas
- `pendiente`
- `en_progreso`
- `completada`

### Prioridades de Tareas
- `baja`
- `media`
- `alta`

## ⚠️ Códigos de Error

| Código | Significado                                    |
|--------|------------------------------------------------|
| 200    | OK - Operación exitosa                         |
| 201    | Created - Recurso creado exitosamente          |
| 400    | Bad Request - Datos inválidos                  |
| 404    | Not Found - Recurso no encontrado              |
| 409    | Conflict - Conflicto (ej: nombre duplicado)    |
| 422    | Unprocessable Entity - Error de validación     |

### Ejemplos de Errores

**404 - Proyecto no encontrado:**
```json
{
  "detail": "Proyecto no encontrado"
}
```

**409 - Nombre duplicado:**
```json
{
  "detail": "Ya existe un proyecto con ese nombre"
}
```

**400 - Proyecto inexistente:**
```json
{
  "detail": "Proyecto no encontrado"
}
```

**422 - Validación fallida:**
```json
{
  "detail": [
    {
      "loc": ["body", "nombre"],
      "msg": "nombre no puede estar vacío",
      "type": "value_error"
    }
  ]
}
```

## 🧪 Ejecutar Tests

```bash
pytest test_TP4.py -v
```

## 📝 Notas Técnicas

### Integridad Referencial

La base de datos garantiza integridad referencial mediante:

1. **Foreign Keys habilitadas**: `PRAGMA foreign_keys = ON`
2. **Cascade Delete**: Al eliminar un proyecto, todas sus tareas se eliminan automáticamente
3. **Validación de existencia**: No se pueden crear tareas con `proyecto_id` inexistente

### Validación de Datos

Toda la validación se realiza mediante modelos Pydantic en `models.py`:
- Nombres y descripciones no pueden estar vacíos
- Estados y prioridades deben ser valores predefinidos
- Nombres de proyectos deben ser únicos

### Base de Datos

La base de datos SQLite (`tareas.db`) se crea automáticamente al iniciar la aplicación si no existe. Las tablas se crean mediante la función `init_db()` en `main.py`.

## 📂 Estructura del Proyecto

```
TP4/
├── main.