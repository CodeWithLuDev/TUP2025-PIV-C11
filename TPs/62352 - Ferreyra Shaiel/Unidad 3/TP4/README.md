# TP4 - API de Gestión de Proyectos y Tareas

API REST desarrollada con FastAPI que permite gestionar proyectos y sus tareas asociadas, implementando relaciones entre tablas y filtros avanzados.

## 📋 Requisitos

- Python 3.8+
- FastAPI
- Uvicorn
- Pydantic
- SQLite3 (incluido en Python)
- Pytest (para tests)

## 🔧 Instalación

```bash
# Instalar dependencias
pip install fastapi uvicorn pydantic pytest

# O usar requirements.txt
pip install -r requirements.txt
```

## 🚀 Iniciar el Servidor

```bash
uvicorn main:app --reload
```

El servidor estará disponible en: `http://localhost:8000`

Documentación interactiva: `http://localhost:8000/docs`

## 🗄️ Estructura de la Base de Datos

### Tabla `proyectos`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | INTEGER | Clave primaria (autoincremental) |
| nombre | TEXT | Nombre del proyecto (único, no nulo) |
| descripcion | TEXT | Descripción opcional |
| fecha_creacion | TEXT | Fecha y hora de creación (ISO format) |

### Tabla `tareas`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | INTEGER | Clave primaria (autoincremental) |
| descripcion | TEXT | Descripción de la tarea (no nulo) |
| estado | TEXT | Estado: pendiente, en_progreso, completada |
| prioridad | TEXT | Prioridad: baja, media, alta |
| proyecto_id | INTEGER | Clave foránea a proyectos.id (no nulo) |
| fecha_creacion | TEXT | Fecha y hora de creación (ISO format) |

**Relación:** Una tarea pertenece a un proyecto (relación 1:N)
- `FOREIGN KEY (proyecto_id) REFERENCES proyectos(id)`
- `ON DELETE CASCADE` - Al eliminar un proyecto, se eliminan sus tareas

## 📡 Endpoints de la API

### **Proyectos**

#### 1. Crear Proyecto
```http
POST /proyectos
Content-Type: application/json

{
  "nombre": "Proyecto Web",
  "descripcion": "Desarrollo de sitio web corporativo"
}
```

**Respuesta (201):**
```json
{
  "id": 1,
  "nombre": "Proyecto Web",
  "descripcion": "Desarrollo de sitio web corporativo",
  "fecha_creacion": "2025-10-23T10:30:00.000000",
  "total_tareas": 0
}
```

#### 2. Listar Proyectos
```http
GET /proyectos
GET /proyectos?nombre=Web  # Filtrar por nombre
```

#### 3. Obtener Proyecto Específico
```http
GET /proyectos/1
```

**Respuesta incluye contador de tareas:**
```json
{
  "id": 1,
  "nombre": "Proyecto Web",
  "descripcion": "Desarrollo de sitio web",
  "fecha_creacion": "2025-10-23T10:30:00.000000",
  "total_tareas": 5
}
```

#### 4. Actualizar Proyecto
```http
PUT /proyectos/1
Content-Type: application/json

{
  "nombre": "Proyecto Web Actualizado",
  "descripcion": "Nueva descripción"
}
```

#### 5. Eliminar Proyecto
```http
DELETE /proyectos/1
```

**Respuesta:**
```json
{
  "mensaje": "Proyecto eliminado exitosamente",
  "tareas_eliminadas": 5
}
```

---

### **Tareas**

#### 1. Crear Tarea en Proyecto
```http
POST /proyectos/1/tareas
Content-Type: application/json

{
  "descripcion": "Diseñar landing page",
  "estado": "pendiente",
  "prioridad": "alta"
}
```

**Respuesta (201):**
```json
{
  "id": 1,
  "descripcion": "Diseñar landing page",
  "estado": "pendiente",
  "prioridad": "alta",
  "proyecto_id": 1,
  "fecha_creacion": "2025-10-23T11:00:00.000000"
}
```

#### 2. Listar Tareas de un Proyecto
```http
GET /proyectos/1/tareas
GET /proyectos/1/tareas?estado=completada
GET /proyectos/1/tareas?prioridad=alta
GET /proyectos/1/tareas?estado=pendiente&prioridad=alta
GET /proyectos/1/tareas?orden=desc
```

#### 3. Listar Todas las Tareas
```http
GET /tareas
GET /tareas?estado=completada
GET /tareas?prioridad=alta
GET /tareas?proyecto_id=1
GET /tareas?estado=pendiente&prioridad=alta&orden=asc
```

#### 4. Actualizar Tarea
```http
PUT /tareas/1
Content-Type: application/json

{
  "descripcion": "Diseñar landing page responsive",
  "estado": "en_progreso",
  "prioridad": "alta",
  "proyecto_id": 2  # Mover a otro proyecto
}
```

#### 5. Eliminar Tarea
```http
DELETE /tareas/1
```

---

### **Resúmenes y Estadísticas**

#### 1. Resumen de Proyecto
```http
GET /proyectos/1/resumen
```

**Respuesta:**
```json
{
  "proyecto_id": 1,
  "proyecto_nombre": "Proyecto Web",
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

#### 2. Resumen General
```http
GET /resumen
```

**Respuesta:**
```json
{
  "total_proyectos": 3,
  "total_tareas": 25,
  "tareas_por_estado": {
    "pendiente": 10,
    "en_progreso": 12,
    "completada": 3
  },
  "proyecto_con_mas_tareas": {
    "id": 1,
    "nombre": "Proyecto Web",
    "cantidad_tareas": 15
  }
}
```

---

## 🧪 Ejecutar Tests

```bash
# Ejecutar todos los tests
pytest test_main.py -v

# Ejecutar un test específico
pytest test_main.py::test_2_1_crear_proyecto_exitoso -v

# Ejecutar con cobertura
pytest test_main.py -v --cov=main
```

## 📝 Ejemplos con cURL

### Crear Proyecto
```bash
curl -X POST http://localhost:8000/proyectos \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "E-commerce",
    "descripcion": "Plataforma de ventas online"
  }'
```

### Crear Tarea
```bash
curl -X POST http://localhost:8000/proyectos/1/tareas \
  -H "Content-Type: application/json" \
  -d '{
    "descripcion": "Implementar carrito de compras",
    "estado": "pendiente",
    "prioridad": "alta"
  }'
```

### Listar con Filtros
```bash
# Tareas completadas de alta prioridad
curl "http://localhost:8000/tareas?estado=completada&prioridad=alta"

# Proyectos que contengan "Web" en el nombre
curl "http://localhost:8000/proyectos?nombre=Web"

# Tareas ordenadas descendentemente
curl "http://localhost:8000/tareas?orden=desc"
```

### Actualizar Tarea
```bash
curl -X PUT http://localhost:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{
    "estado": "completada"
  }'
```

### Obtener Resumen
```bash
# Resumen de un proyecto
curl http://localhost:8000/proyectos/1/resumen

# Resumen general
curl http://localhost:8000/resumen
```

## 🔍 Validaciones Implementadas

### Proyectos
- ✅ Nombre no puede estar vacío
- ✅ Nombre debe ser único
- ✅ Descripción es opcional

### Tareas
- ✅ Descripción no puede estar vacía
- ✅ Estado debe ser: `pendiente`, `en_progreso` o `completada`
- ✅ Prioridad debe ser: `baja`, `media` o `alta`
- ✅ El proyecto asociado debe existir
- ✅ No se pueden crear tareas huérfanas (sin proyecto)

## ⚠️ Códigos de Error

| Código | Descripción |
|--------|-------------|
| 200 | Operación exitosa |
| 201 | Recurso creado exitosamente |
| 400 | Datos inválidos (ej: proyecto_id inexistente) |
| 404 | Recurso no encontrado |
| 409 | Conflicto (ej: nombre duplicado) |
| 422 | Error de validación (ej: estado inválido) |

## 🔐 Integridad Referencial

La base de datos garantiza:

1. **Claves Foráneas Activas**: `PRAGMA foreign_keys = ON`
2. **Eliminación en Cascada**: Al eliminar un proyecto, se eliminan todas sus tareas
3. **Validación de Referencias**: No se pueden crear tareas para proyectos inexistentes
4. **Movimiento de Tareas**: Se puede cambiar el `proyecto_id` de una tarea para moverla

## 📂 Estructura del Proyecto

```
TP4/
├── main.py              # Aplicación principal FastAPI
├── models.py            # Modelos Pydantic de validación
├── test_main.py         # Suite de tests completa
├── tareas.db            # Base de datos SQLite (generada automáticamente)
├── README.md            # Esta documentación
└── requirements.txt     # Dependencias del proyecto
```

## 🛠️ Tecnologías Utilizadas

- **FastAPI**: Framework web moderno y rápido
- **SQLite**: Base de datos relacional embebida
- **Pydantic**: Validación de datos y serialización
- **Uvicorn**: Servidor ASGI para producción
- **Pytest**: Framework de testing

## 📊 Diagrama de Relaciones

```
┌─────────────────────┐
│     PROYECTOS       │
├─────────────────────┤
│ id (PK)             │
│ nombre (UNIQUE)     │
│ descripcion         │
│ fecha_creacion      │
└──────────┬──────────┘
           │
           │ 1:N
           │
           ▼
┌─────────────────────┐
│      TAREAS         │
├─────────────────────┤
│ id (PK)             │
│ descripcion         │
│ estado              │
│ prioridad           │
│ proyecto_id (FK)    │ ───► REFERENCES proyectos(id)
│ fecha_creacion      │      ON DELETE CASCADE
└─────────────────────┘
```

## 💡 Características Principales

✅ CRUD completo para proyectos y tareas
✅ Relaciones 1:N con integridad referencial
✅ Filtros avanzados combinables
✅ Ordenamiento por fecha
✅ Estadísticas y resúmenes
✅ Validación automática con Pydantic
✅ Manejo de errores descriptivo
✅ Eliminación en cascada
✅ Documentación interactiva (Swagger UI)
✅ 100% cobertura de tests

## 🤝 Autor

**Trabajo Práctico N°4**  
Materia: Programación IV  
Fecha de entrega: 24 de Octubre de 2025, 21:00hs

---

## 📞 Soporte

Para problemas o consultas:
- Revisar `/docs` para documentación interactiva
- Verificar que todas las dependencias estén instaladas
- Revisar logs del servidor para errores específicos