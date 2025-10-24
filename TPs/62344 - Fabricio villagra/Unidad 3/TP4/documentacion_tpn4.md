# Trabajo Práctico N°4 - API de Gestión de Proyectos y Tareas

## Descripción

API REST desarrollada con **FastAPI** y **SQLite** que implementa un sistema de gestión de proyectos y tareas con relaciones entre tablas, filtros avanzados y estadísticas.

### Características principales:
- ✅ Relaciones 1:N (un proyecto tiene muchas tareas)
- ✅ Claves foráneas con `ON DELETE CASCADE`
- ✅ CRUD completo para proyectos y tareas
- ✅ Filtros avanzados y búsquedas combinadas
- ✅ Validación con Pydantic
- ✅ Manejo de errores HTTP apropiados
- ✅ Endpoints de estadísticas y resúmenes

---

## Estructura del Proyecto

```
TP4/
├── main.py          # API principal con endpoints
├── models.py        # Modelos Pydantic para validación
├── database.py      # Funciones de base de datos
├── tareas.db        # Base de datos SQLite (se genera automáticamente)
├── test_tp4.py      # Tests automatizados
└── README.md        # Esta documentación
```

---

## Instalación y Ejecución

### Requisitos
- Python 3.9 o superior
- pip (gestor de paquetes de Python)

### 1. Instalar dependencias

```bash
pip install fastapi uvicorn pydantic sqlite3
```

O usando requirements.txt:
```bash
pip install -r requirements.txt
```

### 2. Iniciar el servidor

```bash
python main.py
```

O usando uvicorn directamente:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Acceder a la API

- **API**: http://localhost:8000
- **Documentación interactiva (Swagger)**: http://localhost:8000/docs
- **Documentación alternativa (ReDoc)**: http://localhost:8000/redoc

---

## Estructura de la Base de Datos

### Diagrama de Relaciones

```
┌─────────────────┐         ┌─────────────────┐
│   proyectos     │         │     tareas      │
├─────────────────┤         ├─────────────────┤
│ id (PK)         │◄────────│ id (PK)         │
│ nombre (UNIQUE) │    1:N  │ descripcion     │
│ descripcion     │         │ estado          │
│ fecha_creacion  │         │ prioridad       │
└─────────────────┘         │ proyecto_id (FK)│
                            │ fecha_creacion  │
                            └─────────────────┘
```

### Tabla: `proyectos`

| Campo           | Tipo    | Restricciones        |
|----------------|---------|---------------------|
| id             | INTEGER | PRIMARY KEY, AUTO   |
| nombre         | TEXT    | NOT NULL, UNIQUE    |
| descripcion    | TEXT    | NULL                |
| fecha_creacion | TEXT    | NOT NULL            |

### Tabla: `tareas`

| Campo           | Tipo    | Restricciones                          |
|----------------|---------|---------------------------------------|
| id             | INTEGER | PRIMARY KEY, AUTO                     |
| descripcion    | TEXT    | NOT NULL                              |
| estado         | TEXT    | NOT NULL                              |
| prioridad      | TEXT    | NOT NULL                              |
| proyecto_id    | INTEGER | FOREIGN KEY → proyectos(id), NOT NULL |
| fecha_creacion | TEXT    | NOT NULL                              |

**Importante**: La clave foránea `proyecto_id` tiene configurado `ON DELETE CASCADE`, lo que significa que al eliminar un proyecto se eliminan automáticamente todas sus tareas.

---

## Endpoints de la API

### 📁 Proyectos

#### `GET /proyectos`
Lista todos los proyectos con filtro opcional.

**Query Parameters:**
- `nombre` (opcional): Búsqueda parcial por nombre

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
    "descripcion": "Proyecto de aplicación web",
    "fecha_creacion": "2025-10-23T10:30:00"
  }
]
```

---

#### `GET /proyectos/{id}`
Obtiene un proyecto específico con contador de tareas.

**Ejemplo:**
```bash
curl http://localhost:8000/proyectos/1
```

**Respuesta:**
```json
{
  "id": 1,
  "nombre": "Desarrollo Web",
  "descripcion": "Proyecto de aplicación web",
  "fecha_creacion": "2025-10-23T10:30:00",
  "total_tareas": 15
}
```

---

#### `POST /proyectos`
Crea un nuevo proyecto.

**Body:**
```json
{
  "nombre": "Nuevo Proyecto",
  "descripcion": "Descripción opcional"
}
```

**Ejemplo:**
```bash
curl -X POST http://localhost:8000/proyectos \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Proyecto Alpha", "descripcion": "Mi primer proyecto"}'
```

**Respuesta (201):**
```json
{
  "id": 1,
  "nombre": "Proyecto Alpha",
  "descripcion": "Mi primer proyecto",
  "fecha_creacion": "2025-10-23T10:30:00"
}
```

---

#### `PUT /proyectos/{id}`
Actualiza un proyecto existente.

**Body:**
```json
{
  "nombre": "Nombre actualizado",
  "descripcion": "Nueva descripción"
}
```

**Ejemplo:**
```bash
curl -X PUT http://localhost:8000/proyectos/1 \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Proyecto Beta", "descripcion": "Actualizado"}'
```

---

#### `DELETE /proyectos/{id}`
Elimina un proyecto y todas sus tareas (CASCADE).

**Ejemplo:**
```bash
curl -X DELETE http://localhost:8000/proyectos/1
```

**Respuesta:**
```json
{
  "mensaje": "Proyecto eliminado correctamente",
  "tareas_eliminadas": 5
}
```

---

### ✅ Tareas

#### `GET /tareas`
Lista todas las tareas de todos los proyectos con filtros opcionales.

**Query Parameters:**
- `estado`: `pendiente`, `en_progreso` o `completada`
- `prioridad`: `baja`, `media` o `alta`
- `proyecto_id`: ID del proyecto
- `orden`: `asc` o `desc` (ordenar por fecha de creación)

**Ejemplos:**
```bash
# Todas las tareas
curl http://localhost:8000/tareas

# Tareas completadas
curl http://localhost:8000/tareas?estado=completada

# Tareas de alta prioridad
curl http://localhost:8000/tareas?prioridad=alta

# Tareas completadas de alta prioridad
curl http://localhost:8000/tareas?estado=completada&prioridad=alta

# Tareas de un proyecto específico
curl http://localhost:8000/tareas?proyecto_id=1

# Ordenar descendente (más recientes primero)
curl http://localhost:8000/tareas?orden=desc
```

**Respuesta:**
```json
[
  {
    "id": 1,
    "descripcion": "Implementar login",
    "estado": "completada",
    "prioridad": "alta",
    "proyecto_id": 1,
    "proyecto_nombre": "Desarrollo Web",
    "fecha_creacion": "2025-10-23T10:30:00"
  }
]
```

---

#### `GET /proyectos/{id}/tareas`
Lista todas las tareas de un proyecto específico.

**Query Parameters:**
- `estado`: `pendiente`, `en_progreso` o `completada`
- `prioridad`: `baja`, `media` o `alta`
- `orden`: `asc` o `desc`

**Ejemplo:**
```bash
curl http://localhost:8000/proyectos/1/tareas
curl http://localhost:8000/proyectos/1/tareas?estado=pendiente
```

**Respuesta:**
```json
[
  {
    "id": 1,
    "descripcion": "Crear base de datos",
    "estado": "pendiente",
    "prioridad": "alta",
    "proyecto_id": 1,
    "fecha_creacion": "2025-10-23T10:30:00"
  }
]
```

---

#### `POST /proyectos/{id}/tareas`
Crea una nueva tarea dentro de un proyecto.

**Body:**
```json
{
  "descripcion": "Descripción de la tarea",
  "estado": "pendiente",
  "prioridad": "media"
}
```

**Valores válidos:**
- `estado`: `pendiente` (default), `en_progreso`, `completada`
- `prioridad`: `baja`, `media` (default), `alta`

**Ejemplo:**
```bash
curl -X POST http://localhost:8000/proyectos/1/tareas \
  -H "Content-Type: application/json" \
  -d '{
    "descripcion": "Implementar autenticación",
    "estado": "pendiente",
    "prioridad": "alta"
  }'
```

**Respuesta (201):**
```json
{
  "id": 1,
  "descripcion": "Implementar autenticación",
  "estado": "pendiente",
  "prioridad": "alta",
  "proyecto_id": 1,
  "fecha_creacion": "2025-10-23T10:30:00"
}
```

---

#### `PUT /tareas/{id}`
Actualiza una tarea existente (incluyendo moverla a otro proyecto).

**Body:**
```json
{
  "descripcion": "Nueva descripción",
  "estado": "en_progreso",
  "prioridad": "alta",
  "proyecto_id": 2
}
```

**Ejemplo:**
```bash
curl -X PUT http://localhost:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{"estado": "completada"}'
```

---

#### `DELETE /tareas/{id}`
Elimina una tarea específica.

**Ejemplo:**
```bash
curl -X DELETE http://localhost:8000/tareas/1
```

**Respuesta:**
```json
{
  "mensaje": "Tarea eliminada correctamente"
}
```

---

### 📊 Estadísticas y Resúmenes

#### `GET /proyectos/{id}/resumen`
Obtiene estadísticas detalladas de un proyecto.

**Ejemplo:**
```bash
curl http://localhost:8000/proyectos/1/resumen
```

**Respuesta:**
```json
{
  "proyecto_id": 1,
  "proyecto_nombre": "Desarrollo Web",
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

---

#### `GET /resumen`
Obtiene un resumen general de toda la aplicación.

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
    "nombre": "Desarrollo Web",
    "cantidad_tareas": 15
  }
}
```

---

## Códigos de Error HTTP

| Código | Descripción                           | Ejemplo                                    |
|--------|---------------------------------------|--------------------------------------------|
| 200    | Operación exitosa                     | GET, PUT, DELETE exitosos                  |
| 201    | Recurso creado                        | POST exitoso                               |
| 400    | Datos inválidos                       | Crear tarea con proyecto_id inexistente    |
| 404    | Recurso no encontrado                 | GET de proyecto/tarea que no existe        |
| 409    | Conflicto                             | Crear proyecto con nombre duplicado        |
| 422    | Error de validación                   | Datos que no cumplen validaciones Pydantic |

---

## Validaciones

### Proyectos:
- ✅ El **nombre** no puede estar vacío ni contener solo espacios
- ✅ El **nombre** debe ser único (no puede haber dos proyectos con el mismo nombre)
- ✅ La **descripción** es opcional

### Tareas:
- ✅ La **descripción** no puede estar vacía
- ✅ El **estado** debe ser: `pendiente`, `en_progreso` o `completada`
- ✅ La **prioridad** debe ser: `baja`, `media` o `alta`
- ✅ El **proyecto_id** debe corresponder a un proyecto existente

---

## Integridad Referencial

### ON DELETE CASCADE
Cuando eliminas un proyecto, automáticamente se eliminan todas sus tareas asociadas.

**Ejemplo:**
```bash
# Crear proyecto
curl -X POST http://localhost:8000/proyectos \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Proyecto Temporal"}'

# Crear tareas (proyecto_id = 1)
curl -X POST http://localhost:8000/proyectos/1/tareas \
  -d '{"descripcion": "Tarea 1"}'

# Eliminar proyecto (elimina automáticamente todas sus tareas)
curl -X DELETE http://localhost:8000/proyectos/1
```

### Validación de Claves Foráneas
No puedes crear una tarea con un `proyecto_id` que no existe:

```bash
# Esto devuelve error 400
curl -X POST http://localhost:8000/proyectos/999/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Tarea huérfana"}'
```

---

## Ejemplos de Uso Completos

### Ejemplo 1: Crear proyecto con tareas

```bash
# 1. Crear proyecto
curl -X POST http://localhost:8000/proyectos \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Tienda Online",
    "descripcion": "E-commerce de productos"
  }'

# Respuesta: {"id": 1, ...}

# 2. Crear tareas
curl -X POST http://localhost:8000/proyectos/1/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Diseñar base de datos", "prioridad": "alta"}'

curl -X POST http://localhost:8000/proyectos/1/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Crear API REST", "prioridad": "alta"}'

curl -X POST http://localhost:8000/proyectos/1/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Implementar frontend", "prioridad": "media"}'

# 3. Ver tareas del proyecto
curl http://localhost:8000/proyectos/1/tareas

# 4. Ver resumen del proyecto
curl http://localhost:8000/proyectos/1/resumen
```

### Ejemplo 2: Buscar y filtrar tareas

```bash
# Buscar todas las tareas pendientes de alta prioridad
curl "http://localhost:8000/tareas?estado=pendiente&prioridad=alta"

# Ver tareas más recientes primero
curl "http://localhost:8000/tareas?orden=desc"

# Tareas completadas de un proyecto específico
curl "http://localhost:8000/proy