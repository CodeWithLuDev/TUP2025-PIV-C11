# API de Proyectos y Tareas - TP4

## Descripción

API REST desarrollada con FastAPI que permite gestionar proyectos y sus tareas asociadas, implementando relaciones 1:N (uno a muchos) entre tablas usando SQLite con claves foráneas y CASCADE.

## Características

- Gestión completa de proyectos (CRUD)
- Gestión de tareas asociadas a proyectos
- Relaciones 1:N con integridad referencial
- Eliminación en cascada (CASCADE)
- Filtros avanzados y búsquedas combinables
- Resúmenes estadísticos por proyecto y generales
- Validaciones con Pydantic
- Persistencia de datos en SQLite

## Tecnologías Utilizadas

- FastAPI: Framework web asincrónico
- SQLite: Base de datos relacional con claves foráneas
- Pydantic: Validación de datos y modelos
- Python 3.8+: Lenguaje de programación

## Estructura del Proyecto

```
TP4/
├── main.py              # API principal con endpoints
├── models.py            # Modelos Pydantic para validación
├── database.py          # Funciones de base de datos
├── tareas.db            # Base de datos SQLite (se crea automáticamente)
├── test_TP4.py          # Tests unitarios
└── README.md            # Este archivo
```

## Instalación

### 1. Requisitos previos

Asegúrate de tener Python 3.8 o superior instalado.

### 2. Instalar dependencias

```bash
pip install fastapi uvicorn pydantic pytest
```

### 3. Iniciar el servidor

```bash
uvicorn main:app --reload
```

El servidor estará disponible en: http://localhost:8000

Documentación interactiva (Swagger): http://localhost:8000/docs

## Estructura de la Base de Datos

### Diagrama de Relaciones

```
┌─────────────────┐
│   proyectos     │
├─────────────────┤
│ id (PK)         │
│ nombre (UNIQUE) │
│ descripcion     │
│ fecha_creacion  │
└────────┬────────┘
         │
         │ 1:N
         │
         │
┌────────┴────────┐
│     tareas      │
├─────────────────┤
│ id (PK)         │
│ descripcion     │
│ estado          │
│ prioridad       │
│ proyecto_id (FK)│ ──> ON DELETE CASCADE
│ fecha_creacion  │
└─────────────────┘
```

### Tabla: proyectos

| Campo          | Tipo    | Restricciones            |
|----------------|---------|--------------------------|
| id             | INTEGER | PRIMARY KEY, AUTOINCREMENT |
| nombre         | TEXT    | NOT NULL, UNIQUE         |
| descripcion    | TEXT    | NULL                     |
| fecha_creacion | TEXT    | NOT NULL                 |

### Tabla: tareas

| Campo          | Tipo    | Restricciones                              |
|----------------|---------|--------------------------------------------|
| id             | INTEGER | PRIMARY KEY, AUTOINCREMENT                 |
| descripcion    | TEXT    | NOT NULL                                   |
| estado         | TEXT    | NOT NULL                                   |
| prioridad      | TEXT    | NOT NULL                                   |
| proyecto_id    | INTEGER | NOT NULL, FOREIGN KEY → proyectos(id)     |
| fecha_creacion | TEXT    | NOT NULL                                   |

**Nota importante:** La relación tiene `ON DELETE CASCADE`, lo que significa que al eliminar un proyecto se eliminan automáticamente todas sus tareas asociadas.

## Endpoints de la API

### Proyectos

#### 1. Crear un proyecto

```http
POST /proyectos
Content-Type: application/json

{
  "nombre": "Proyecto Alpha",
  "descripcion": "Descripción del proyecto"
}
```

**Respuesta (201 Created):**
```json
{
  "id": 1,
  "nombre": "Proyecto Alpha",
  "descripcion": "Descripción del proyecto",
  "fecha_creacion": "2025-10-24T15:30:00.123456"
}
```

**Validaciones:**
- `nombre`: Obligatorio, no puede estar vacío, debe ser único
- `descripcion`: Opcional

**Errores:**
- `409`: Nombre duplicado
- `422`: Validación fallida (nombre vacío)

---

#### 2. Listar todos los proyectos

```http
GET /proyectos
```

**Con filtro por nombre:**
```http
GET /proyectos?nombre=Alpha
```

**Respuesta (200 OK):**
```json
[
  {
    "id": 1,
    "nombre": "Proyecto Alpha",
    "descripcion": "Descripción del proyecto",
    "fecha_creacion": "2025-10-24T15:30:00.123456"
  }
]
```

---

#### 3. Obtener un proyecto específico

```http
GET /proyectos/1
```

**Respuesta (200 OK):**
```json
{
  "id": 1,
  "nombre": "Proyecto Alpha",
  "descripcion": "Descripción del proyecto",
  "fecha_creacion": "2025-10-24T15:30:00.123456",
  "total_tareas": 5
}
```

**Errores:**
- `404`: Proyecto no encontrado

---

#### 4. Actualizar un proyecto

```http
PUT /proyectos/1
Content-Type: application/json

{
  "nombre": "Proyecto Alpha Modificado",
  "descripcion": "Nueva descripción"
}
```

**Respuesta (200 OK):**
```json
{
  "id": 1,
  "nombre": "Proyecto Alpha Modificado",
  "descripcion": "Nueva descripción",
  "fecha_creacion": "2025-10-24T15:30:00.123456"
}
```

**Errores:**
- `404`: Proyecto no encontrado
- `409`: Nombre duplicado

---

#### 5. Eliminar un proyecto

```http
DELETE /proyectos/1
```

**Respuesta (200 OK):**
```json
{
  "mensaje": "Proyecto 1 eliminado correctamente",
  "tareas_eliminadas": 5
}
```

**Nota:** Al eliminar un proyecto, todas sus tareas se eliminan automáticamente (CASCADE).

**Errores:**
- `404`: Proyecto no encontrado

---

### Tareas

#### 6. Crear una tarea en un proyecto

```http
POST /proyectos/1/tareas
Content-Type: application/json

{
  "descripcion": "Implementar API REST",
  "estado": "pendiente",
  "prioridad": "alta"
}
```

**Campos:**
- `descripcion` (string, obligatorio): Descripción de la tarea
- `estado` (string, opcional): `pendiente`, `en_progreso`, `completada` (default: `pendiente`)
- `prioridad` (string, opcional): `baja`, `media`, `alta` (default: `media`)

**Respuesta (201 Created):**
```json
{
  "id": 1,
  "descripcion": "Implementar API REST",
  "estado": "pendiente",
  "prioridad": "alta",
  "proyecto_id": 1,
  "fecha_creacion": "2025-10-24T15:35:00.123456"
}
```

**Errores:**
- `400`: Proyecto no existe
- `422`: Validación fallida

---

#### 7. Listar tareas de un proyecto

```http
GET /proyectos/1/tareas
```

**Respuesta (200 OK):**
```json
[
  {
    "id": 1,
    "descripcion": "Implementar API REST",
    "estado": "pendiente",
    "prioridad": "alta",
    "proyecto_id": 1,
    "fecha_creacion": "2025-10-24T15:35:00.123456"
  }
]
```

**Errores:**
- `404`: Proyecto no encontrado

---

#### 8. Listar todas las tareas

```http
GET /tareas
```

**Con filtros:**
```http
GET /tareas?estado=pendiente&prioridad=alta&proyecto_id=1&orden=desc
```

**Filtros disponibles:**
- `estado`: Filtrar por estado (`pendiente`, `en_progreso`, `completada`)
- `prioridad`: Filtrar por prioridad (`baja`, `media`, `alta`)
- `proyecto_id`: Filtrar por proyecto específico
- `orden`: Ordenar por fecha (`asc` o `desc`)

**Los filtros son combinables.**

**Respuesta (200 OK):**
```json
[
  {
    "id": 1,
    "descripcion": "Implementar API REST",
    "estado": "pendiente",
    "prioridad": "alta",
    "proyecto_id": 1,
    "fecha_creacion": "2025-10-24T15:35:00.123456"
  }
]
```

---

#### 9. Actualizar una tarea

```http
PUT /tareas/1
Content-Type: application/json

{
  "descripcion": "Implementar API REST - Actualizado",
  "estado": "en_progreso",
  "prioridad": "alta",
  "proyecto_id": 2
}
```

**Campos opcionales:**
- `descripcion`: Nueva descripción
- `estado`: Nuevo estado
- `prioridad`: Nueva prioridad
- `proyecto_id`: Mover a otro proyecto

**Respuesta (200 OK):**
```json
{
  "id": 1,
  "descripcion": "Implementar API REST - Actualizado",
  "estado": "en_progreso",
  "prioridad": "alta",
  "proyecto_id": 2,
  "fecha_creacion": "2025-10-24T15:35:00.123456"
}
```

**Errores:**
- `404`: Tarea no encontrada
- `400`: Proyecto destino no existe

---

#### 10. Eliminar una tarea

```http
DELETE /tareas/1
```

**Respuesta (200 OK):**
```json
{
  "mensaje": "Tarea 1 eliminada correctamente"
}
```

**Errores:**
- `404`: Tarea no encontrada

---

### Resúmenes y Estadísticas

#### 11. Resumen de un proyecto

```http
GET /proyectos/1/resumen
```

**Respuesta (200 OK):**
```json
{
  "proyecto_id": 1,
  "proyecto_nombre": "Proyecto Alpha",
  "total_tareas": 10,
  "por_estado": {
    "pendiente": 3,
    "en_progreso": 5,
    "completada": 2
  },
  "por_prioridad": {
    "baja": 2,
    "media": 5,
    "alta": 3
  }
}
```

**Errores:**
- `404`: Proyecto no encontrado

---

#### 12. Resumen general

```http
GET /resumen
```

**Respuesta (200 OK):**
```json
{
  "total_proyectos": 3,
  "total_tareas": 25,
  "tareas_por_estado": {
    "pendiente": 8,
    "en_progreso": 12,
    "completada": 5
  },
  "proyecto_con_mas_tareas": {
    "id": 1,
    "nombre": "Proyecto Alpha",
    "cantidad_tareas": 10
  }
}
```

---

## Ejemplos con cURL

### Crear un proyecto

```bash
curl -X POST http://localhost:8000/proyectos \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Mi Proyecto", "descripcion": "Descripción del proyecto"}'
```

### Listar proyectos

```bash
curl http://localhost:8000/proyectos
```

### Buscar proyectos por nombre

```bash
curl "http://localhost:8000/proyectos?nombre=Alpha"
```

### Crear una tarea

```bash
curl -X POST http://localhost:8000/proyectos/1/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Mi tarea", "estado": "pendiente", "prioridad": "alta"}'
```

### Listar tareas con filtros

```bash
curl "http://localhost:8000/tareas?estado=pendiente&prioridad=alta&orden=desc"
```

### Actualizar una tarea

```bash
curl -X PUT http://localhost:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{"estado": "completada"}'
```

### Mover una tarea a otro proyecto

```bash
curl -X PUT http://localhost:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{"proyecto_id": 2}'
```

### Eliminar un proyecto

```bash
curl -X DELETE http://localhost:8000/proyectos/1
```

### Obtener resumen de proyecto

```bash
curl http://localhost:8000/proyectos/1/resumen
```

### Obtener resumen general

```bash
curl http://localhost:8000/resumen
```

---

## Validaciones

### Proyectos

| Campo | Validación |
|-------|-----------|
| nombre | No puede estar vacío, no solo espacios, debe ser único |
| descripcion | Opcional |

### Tareas

| Campo | Validación |
|-------|-----------|
| descripcion | No puede estar vacía, no solo espacios |
| estado | Debe ser: `pendiente`, `en_progreso` o `completada` |
| prioridad | Debe ser: `baja`, `media` o `alta` |
| proyecto_id | Debe existir en la tabla proyectos |

---

## Códigos de Estado HTTP

| Código | Significado |
|--------|------------|
| 200 | OK - Solicitud exitosa |
| 201 | Created - Recurso creado exitosamente |
| 400 | Bad Request - Datos inválidos (ej: proyecto_id inexistente) |
| 404 | Not Found - Recurso no encontrado |
| 409 | Conflict - Conflicto (ej: nombre de proyecto duplicado) |
| 422 | Unprocessable Entity - Validación de Pydantic fallida |
| 500 | Internal Server Error - Error del servidor |

---

## Integridad Referencial

La API garantiza integridad referencial mediante:

1. **Claves foráneas (Foreign Keys)**: `proyecto_id` en la tabla `tareas` referencia a `proyectos.id`
2. **ON DELETE CASCADE**: Al eliminar un proyecto, todas sus tareas se eliminan automáticamente
3. **Validaciones**: No se pueden crear tareas con `proyecto_id` inexistente
4. **Nombres únicos**: No pueden existir dos proyectos con el mismo nombre

### Ejemplo de CASCADE:

```bash
# Crear proyecto
curl -X POST http://localhost:8000/proyectos \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Proyecto Temporal"}'
# Respuesta: {"id": 5, ...}

# Crear 3 tareas en el proyecto
curl -X POST http://localhost:8000/proyectos/5/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Tarea 1"}'

curl -X POST http://localhost:8000/proyectos/5/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Tarea 2"}'

curl -X POST http://localhost:8000/proyectos/5/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Tarea 3"}'

# Eliminar el proyecto
curl -X DELETE http://localhost:8000/proyectos/5
# Respuesta: {"mensaje": "...", "tareas_eliminadas": 3}

# Las 3 tareas también fueron eliminadas (CASCADE)
curl http://localhost:8000/tareas
# Las tareas con proyecto_id=5 ya no existen
```

---

## Testeo

### Ejecutar todos los tests

```bash
pytest test_TP4.py -v
```

### Ejecutar un test específico

```bash
pytest test_TP4.py::test_2_1_crear_proyecto_exitoso -v
```

### Ejecutar tests con salida detallada

```bash
pytest test_TP4.py -v -s
```

### Parar en el primer error

```bash
pytest test_TP4.py -v -x
```

Total de tests: 50+ tests unitarios que cubren todos los endpoints y casos de uso.

---

## Notas Importantes

- La base de datos `tareas.db` se crea automáticamente al iniciar la aplicación
- Las claves foráneas están habilitadas con `PRAGMA foreign_keys = ON`
- Los timestamps están en formato ISO 8601
- Los filtros en las búsquedas son case-sensitive
- Al eliminar un proyecto, todas sus tareas se eliminan automáticamente (CASCADE)
- Los nombres de proyectos deben ser únicos
- No se pueden crear tareas con `proyecto_id` inexistente

---

## Arquitectura del Código

### main.py
Contiene toda la lógica de endpoints y manejo de peticiones HTTP.

### models.py
Define los modelos Pydantic para validación de datos:
- `ProyectoCreate`, `ProyectoResponse`, `ProyectoConTareas`
- `TareaCreate`, `TareaUpdate`, `TareaResponse`

### database.py
Gestiona la conexión y estructura de la base de datos:
- `init_db()`: Crea las tablas con relaciones
- `obtener_conexion()`: Devuelve conexión con FK habilitadas

---

## Solución de Problemas

### Error: "cannot import name 'DB_NAME'"
Asegúrate de que `database.py` exporta `DB_NAME` y que `main.py` lo importa.

### Error: "foreign key constraint failed"
Verifica que el `proyecto_id` que estás usando existe en la tabla proyectos.

### Error: "UNIQUE constraint failed"
Ya existe un proyecto con ese nombre. Usa otro nombre o actualiza el proyecto existente.

### La base de datos no se crea
Verifica que tienes permisos de escritura en la carpeta del proyecto.

---

## Autor

Trabajo Práctico N°4 - Backend con FastAPI, SQLite y Relaciones

## Fecha

Octubre 2025