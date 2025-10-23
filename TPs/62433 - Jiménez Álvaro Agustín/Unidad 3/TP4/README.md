# TP4 - Relaciones entre Tablas y Filtros Avanzados

## Descripción
API REST desarrollada con FastAPI que gestiona **proyectos y tareas** con relaciones entre tablas usando SQLite. Implementa relaciones 1:N (uno a muchos) con claves foráneas y consultas complejas usando JOINs.

## Características
- ✅ Relación 1:N entre Proyectos y Tareas
- ✅ CRUD completo para Proyectos y Tareas
- ✅ Integridad referencial con claves foráneas
- ✅ CASCADE DELETE (eliminar proyecto elimina sus tareas)
- ✅ Filtros avanzados combinables
- ✅ Consultas con JOINs
- ✅ Estadísticas y resúmenes por proyecto
- ✅ Validaciones con Pydantic
- ✅ Arquitectura modular (models, database, main)

## Estructura de la Base de Datos

### Tabla: proyectos
| Campo | Tipo | Restricciones |
|-------|------|---------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT |
| nombre | TEXT | NOT NULL, UNIQUE |
| descripcion | TEXT | NULL |
| fecha_creacion | TEXT | NOT NULL |

### Tabla: tareas
| Campo | Tipo | Restricciones |
|-------|------|---------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT |
| descripcion | TEXT | NOT NULL |
| estado | TEXT | NOT NULL |
| prioridad | TEXT | NOT NULL |
| proyecto_id | INTEGER | FOREIGN KEY → proyectos(id), ON DELETE CASCADE |
| fecha_creacion | TEXT | NOT NULL |

### Relación
- **1 Proyecto** puede tener **muchas Tareas** (1:N)
- Al eliminar un proyecto, se eliminan automáticamente todas sus tareas (CASCADE)

## Requisitos
- Python 3.8+
- FastAPI
- Uvicorn
- Pydantic

## Instalación

### 1. Instalar dependencias
```bash
pip install fastapi uvicorn pydantic
```

### 2. Iniciar el servidor
```bash
python -m uvicorn main:app --reload
```

El servidor estará disponible en: `http://127.0.0.1:8000`

### 3. Documentación interactiva
- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

## Estructura del Proyecto
```
TP4/
├── main.py          # API principal con endpoints
├── models.py        # Modelos Pydantic para validación
├── database.py      # Funciones de base de datos
├── tareas.db        # Base de datos SQLite (se crea automáticamente)
└── README.md        # Este archivo
```

## Endpoints

### 📊 Raíz
```
GET /
```
Información general de la API

---

## 🗂️ Endpoints de Proyectos

### 1. Listar todos los proyectos
```bash
GET /proyectos
```

**Query Parameters:**
- `nombre` (opcional): Buscar proyectos por nombre parcial

**Ejemplos:**
```bash
# Todos los proyectos
curl http://127.0.0.1:8000/proyectos

# Buscar por nombre
curl http://127.0.0.1:8000/proyectos?nombre=alpha
```

**Respuesta:**
```json
[
  {
    "id": 1,
    "nombre": "Proyecto Alpha",
    "descripcion": "Proyecto de prueba",
    "fecha_creacion": "2025-10-23T10:30:00",
    "total_tareas": 5
  }
]
```

### 2. Obtener un proyecto específico
```bash
GET /proyectos/{proyecto_id}
```

**Ejemplo:**
```bash
curl http://127.0.0.1:8000/proyectos/1
```

### 3. Crear un proyecto
```bash
POST /proyectos
```

**Body (JSON):**
```json
{
  "nombre": "Proyecto Beta",
  "descripcion": "Descripción opcional"
}
```

**Ejemplo con curl:**
```bash
curl -X POST http://127.0.0.1:8000/proyectos \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Proyecto Beta",
    "descripcion": "Mi nuevo proyecto"
  }'
```

### 4. Actualizar un proyecto
```bash
PUT /proyectos/{proyecto_id}
```

**Body (JSON):**
```json
{
  "nombre": "Proyecto Beta Actualizado",
  "descripcion": "Nueva descripción"
}
```

**Ejemplo:**
```bash
curl -X PUT http://127.0.0.1:8000/proyectos/1 \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Proyecto Actualizado"
  }'
```

### 5. Eliminar un proyecto
```bash
DELETE /proyectos/{proyecto_id}
```

⚠️ **Importante**: Al eliminar un proyecto, se eliminan automáticamente todas sus tareas (CASCADE)

**Ejemplo:**
```bash
curl -X DELETE http://127.0.0.1:8000/proyectos/1
```

---

## 📝 Endpoints de Tareas

### 6. Listar todas las tareas
```bash
GET /tareas
```

**Query Parameters (todos opcionales y combinables):**
- `estado`: `pendiente`, `en_progreso`, `completada`
- `prioridad`: `baja`, `media`, `alta`
- `proyecto_id`: ID del proyecto
- `texto`: Buscar en la descripción
- `orden`: `asc` o `desc` (por fecha de creación)

**Ejemplos:**
```bash
# Todas las tareas
curl http://127.0.0.1:8000/tareas

# Filtrar por estado
curl http://127.0.0.1:8000/tareas?estado=pendiente

# Filtrar por prioridad
curl http://127.0.0.1:8000/tareas?prioridad=alta

# Filtrar por proyecto
curl http://127.0.0.1:8000/tareas?proyecto_id=1

# Múltiples filtros combinados
curl "http://127.0.0.1:8000/tareas?estado=completada&prioridad=alta&orden=desc"

# Buscar por texto
curl http://127.0.0.1:8000/tareas?texto=implementar
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
    "proyecto_nombre": "Proyecto Alpha",
    "fecha_creacion": "2025-10-23T10:35:00"
  }
]
```

### 7. Listar tareas de un proyecto específico
```bash
GET /proyectos/{proyecto_id}/tareas
```

**Query Parameters:**
- `estado` (opcional)
- `prioridad` (opcional)
- `orden` (opcional)

**Ejemplos:**
```bash
# Todas las tareas del proyecto 1
curl http://127.0.0.1:8000/proyectos/1/tareas

# Tareas pendientes del proyecto 1
curl http://127.0.0.1:8000/proyectos/1/tareas?estado=pendiente

# Tareas de alta prioridad ordenadas
curl "http://127.0.0.1:8000/proyectos/1/tareas?prioridad=alta&orden=desc"
```

### 8. Crear una tarea en un proyecto
```bash
POST /proyectos/{proyecto_id}/tareas
```

**Body (JSON):**
```json
{
  "descripcion": "Implementar login",
  "estado": "pendiente",
  "prioridad": "alta"
}
```

**Ejemplo:**
```bash
curl -X POST http://127.0.0.1:8000/proyectos/1/tareas \
  -H "Content-Type: application/json" \
  -d '{
    "descripcion": "Implementar autenticación",
    "estado": "en_progreso",
    "prioridad": "alta"
  }'
```

### 9. Obtener una tarea específica
```bash
GET /tareas/{tarea_id}
```

**Ejemplo:**
```bash
curl http://127.0.0.1:8000/tareas/1
```

### 10. Actualizar una tarea
```bash
PUT /tareas/{tarea_id}
```

**Body (JSON):**
```json
{
  "descripcion": "Nueva descripción",
  "estado": "completada",
  "prioridad": "media",
  "proyecto_id": 2
}
```

⚠️ **Nota**: Puedes cambiar el `proyecto_id` para mover la tarea a otro proyecto

**Ejemplo:**
```bash
curl -X PUT http://127.0.0.1:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{
    "estado": "completada"
  }'
```

### 11. Eliminar una tarea
```bash
DELETE /tareas/{tarea_id}
```

**Ejemplo:**
```bash
curl -X DELETE http://127.0.0.1:8000/tareas/1
```

---

## 📈 Endpoints de Resumen y Estadísticas

### 12. Resumen de un proyecto
```bash
GET /proyectos/{proyecto_id}/resumen
```

**Ejemplo:**
```bash
curl http://127.0.0.1:8000/proyectos/1/resumen
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

### 13. Resumen general
```bash
GET /resumen
```

**Ejemplo:**
```bash
curl http://127.0.0.1:8000/resumen
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

---

## Validaciones

### Estados válidos
- `pendiente`
- `en_progreso`
- `completada`

### Prioridades válidas
- `baja`
- `media`
- `alta`

### Reglas de validación
- ✅ El nombre del proyecto no puede estar vacío
- ✅ El nombre del proyecto debe ser único
- ✅ La descripción de la tarea no puede estar vacía
- ✅ El `proyecto_id` debe existir al crear/actualizar tareas
- ✅ No se pueden crear tareas en proyectos inexistentes

---

## Códigos de Error

| Código | Descripción |
|--------|-------------|
| 400 | Datos inválidos (ej: proyecto_id inexistente) |
| 404 | Recurso no encontrado (proyecto o tarea) |
| 409 | Conflicto (ej: nombre de proyecto duplicado) |

---

## Verificación de Integridad Referencial

### Prueba 1: Crear proyecto y tareas
```bash
# 1. Crear proyecto
curl -X POST http://127.0.0.1:8000/proyectos \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Test Project"}'

# 2. Crear tareas en el proyecto
curl -X POST http://127.0.0.1:8000/proyectos/1/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Tarea 1", "estado": "pendiente", "prioridad": "alta"}'
```

### Prueba 2: Intentar crear tarea en proyecto inexistente (debe fallar)
```bash
curl -X POST http://127.0.0.1:8000/proyectos/999/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Esto fallará", "estado": "pendiente", "prioridad": "media"}'
```

### Prueba 3: CASCADE DELETE
```bash
# 1. Ver tareas del proyecto
curl http://127.0.0.1:8000/proyectos/1/tareas

# 2. Eliminar el proyecto
curl -X DELETE http://127.0.0.1:8000/proyectos/1

# 3. Verificar que las tareas también se eliminaron
curl http://127.0.0.1:8000/tareas?proyecto_id=1
```

### Prueba 4: Mover tarea a otro proyecto
```bash
curl -X PUT http://127.0.0.1:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{"proyecto_id": 2}'
```

---

## Testing

### Instalar dependencias de testing
```bash
pip install pytest requests httpx
```

### Ejecutar tests
```bash
# Todos los tests
pytest test_TP4.py -v

# Un test específico
pytest test_TP4.py::test_crear_proyecto -v
```

---

## Ejemplo de Uso Completo

```bash
# 1. Crear un proyecto
curl -X POST http://127.0.0.1:8000/proyectos \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Mi Proyecto", "descripcion": "Proyecto de ejemplo"}'

# 2. Crear tareas en el proyecto (asumiendo ID=1)
curl -X POST http://127.0.0.1:8000/proyectos/1/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Diseñar interfaz", "estado": "pendiente", "prioridad": "alta"}'

curl -X POST http://127.0.0.1:8000/proyectos/1/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Implementar backend", "estado": "en_progreso", "prioridad": "alta"}'

# 3. Ver todas las tareas del proyecto
curl http://127.0.0.1:8000/proyectos/1/tareas

# 4. Ver resumen del proyecto
curl http://127.0.0.1:8000/proyectos/1/resumen

# 5. Actualizar estado de una tarea
curl -X PUT http://127.0.0.1:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{"estado": "completada"}'

# 6. Ver resumen general
curl http://127.0.0.1:8000/resumen
```

---

## Autor
**Jiménez Álvaro Agustín**  
Legajo: 62433

---

## Notas Adicionales

- La base de datos `tareas.db` se crea automáticamente al iniciar el servidor
- Las claves foráneas están habilitadas con `PRAGMA foreign_keys = ON`
- La integridad referencial se mantiene en todo momento
- El código está modularizado para facilitar el mantenimiento