# TP4 - Relaciones entre Tablas y Filtros Avanzados

## 📋 Descripción

Este es un trabajo practicos sobre una API REST desarrollada con FastAPI para la gestión de proyectos y tareas. Implementa relaciones 1:N entre tablas usando SQLite, con validaciones, filtros avanzados y estadísticas.

## 🗃️ Estructura de la Base de Datos

### Diagrama de Relación

```
┌─────────────────────┐         ┌─────────────────────┐
│     PROYECTOS       │         │       TAREAS        │
├─────────────────────┤         ├─────────────────────┤
│ id (PK)             │────┐    │ id (PK)             │
│ nombre (UNIQUE)     │    │    │ descripcion         │
│ descripcion         │    │    │ estado              │
│ fecha_creacion      │    │    │ prioridad           │
└─────────────────────┘    │    │ proyecto_id (FK)    │
                           └───>│ fecha_creacion      │
                      1:N       └─────────────────────┘
```

### Tabla `proyectos`

| Campo          | Tipo    | Restricciones                    |
|----------------|---------|----------------------------------|
| id             | INTEGER | PRIMARY KEY, AUTOINCREMENT       |
| nombre         | TEXT    | NOT NULL, UNIQUE                 |
| descripcion    | TEXT    | NULL                             |
| fecha_creacion | TEXT    | NOT NULL                         |

### Tabla `tareas`

| Campo          | Tipo    | Restricciones                              |
|----------------|---------|--------------------------------------------|
| id             | INTEGER | PRIMARY KEY, AUTOINCREMENT                 |
| descripcion    | TEXT    | NOT NULL                                   |
| estado         | TEXT    | NOT NULL                                   |
| prioridad      | TEXT    | NOT NULL                                   |
| proyecto_id    | INTEGER | NOT NULL, FOREIGN KEY ON DELETE CASCADE    |
| fecha_creacion | TEXT    | NOT NULL                                   |

**Integridad Referencial:**
- La columna `proyecto_id` en `tareas` referencia a `proyectos.id`
- Configurado con `ON DELETE CASCADE`: al eliminar un proyecto, se eliminan automáticamente todas sus tareas asociadas

## 🚀 Instalación y Ejecución

### Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Instalación

1. **Clonar o descargar el proyecto:**
   ```bash
   cd TP4
   ```

2. **Crear un entorno virtual (recomendado):**
   ```bash
   python -m venv venv
   ```

3. **Activar el entorno virtual:**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. **Instalar dependencias:**
   ```bash
   pip install fastapi uvicorn sqlite3 pydantic
   ```

### Iniciar el Servidor

```bash
python main.py
```

O usando uvicorn directamente:
```bash
uvicorn main:app --reload
```

El servidor estará disponible en: `http://localhost:8000`

## 📚 Documentación de la API

### Documentación Interactiva

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## 🔌 Endpoints Disponibles

### Proyectos

#### 1. Crear Proyecto
```bash
POST /proyectos
Content-Type: application/json

{
  "nombre": "Proyecto Alpha",
  "descripcion": "Descripción del proyecto"
}
```

**Respuesta (201):**
```json
{
  "id": 1,
  "nombre": "Proyecto Alpha",
  "descripcion": "Descripción del proyecto",
  "fecha_creacion": "2025-10-23T10:30:00.123456"
}
```

#### 2. Listar Proyectos
```bash
GET /proyectos
GET /proyectos?nombre=Alpha  # Filtrar por nombre
```

**Respuesta (200):**
```json
[
  {
    "id": 1,
    "nombre": "Proyecto Alpha",
    "descripcion": "Descripción del proyecto",
    "fecha_creacion": "2025-10-23T10:30:00.123456"
  }
]
```

#### 3. Obtener Proyecto Específico
```bash
GET /proyectos/{id}
```

**Respuesta (200):**
```json
{
  "id": 1,
  "nombre": "Proyecto Alpha",
  "descripcion": "Descripción del proyecto",
  "fecha_creacion": "2025-10-23T10:30:00.123456",
  "total_tareas": 5
}
```

#### 4. Actualizar Proyecto
```bash
PUT /proyectos/{id}
Content-Type: application/json

{
  "nombre": "Proyecto Alpha Modificado",
  "descripcion": "Nueva descripción"
}
```

#### 5. Eliminar Proyecto
```bash
DELETE /proyectos/{id}
```

**Respuesta (200):**
```json
{
  "mensaje": "Proyecto eliminado",
  "tareas_eliminadas": 5
}
```

### Tareas

#### 6. Crear Tarea en Proyecto
```bash
POST /proyectos/{proyecto_id}/tareas
Content-Type: application/json

{
  "descripcion": "Implementar login",
  "estado": "pendiente",
  "prioridad": "alta"
}
```

**Estados válidos:** `pendiente`, `en_progreso`, `completada`  
**Prioridades válidas:** `baja`, `media`, `alta`

**Respuesta (201):**
```json
{
  "id": 1,
  "descripcion": "Implementar login",
  "estado": "pendiente",
  "prioridad": "alta",
  "proyecto_id": 1,
  "fecha_creacion": "2025-10-23T10:35:00.123456"
}
```

#### 7. Listar Tareas de un Proyecto
```bash
GET /proyectos/{proyecto_id}/tareas
GET /proyectos/{proyecto_id}/tareas?estado=pendiente
GET /proyectos/{proyecto_id}/tareas?prioridad=alta
GET /proyectos/{proyecto_id}/tareas?estado=pendiente&prioridad=alta
GET /proyectos/{proyecto_id}/tareas?orden=desc
```

#### 8. Listar Todas las Tareas
```bash
GET /tareas
GET /tareas?proyecto_id=1
GET /tareas?estado=completada
GET /tareas?prioridad=alta
GET /tareas?estado=completada&prioridad=alta
GET /tareas?orden=asc
```

#### 9. Actualizar Tarea
```bash
PUT /tareas/{id}
Content-Type: application/json

{
  "descripcion": "Implementar login con OAuth",
  "estado": "en_progreso",
  "prioridad": "alta",
  "proyecto_id": 2
}
```

#### 10. Eliminar Tarea
```bash
DELETE /tareas/{id}
```

### Estadísticas

#### 11. Resumen de Proyecto
```bash
GET /proyectos/{proyecto_id}/resumen
```

**Respuesta (200):**
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

#### 12. Resumen General
```bash
GET /resumen
```

**Respuesta (200):**
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

## 📝 Ejemplos con cURL

### Crear un Proyecto
```bash
curl -X POST "http://localhost:8000/proyectos" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Mi Proyecto",
    "descripcion": "Descripción de mi proyecto"
  }'
```

### Listar Proyectos
```bash
curl -X GET "http://localhost:8000/proyectos"
```

### Buscar Proyectos por Nombre
```bash
curl -X GET "http://localhost:8000/proyectos?nombre=Desarrollo"
```

### Crear Tarea en Proyecto
```bash
curl -X POST "http://localhost:8000/proyectos/1/tareas" \
  -H "Content-Type: application/json" \
  -d '{
    "descripcion": "Crear base de datos",
    "estado": "pendiente",
    "prioridad": "alta"
  }'
```

### Listar Tareas con Filtros
```bash
curl -X GET "http://localhost:8000/tareas?estado=completada&prioridad=alta"
```

### Actualizar Tarea
```bash
curl -X PUT "http://localhost:8000/tareas/1" \
  -H "Content-Type: application/json" \
  -d '{
    "estado": "completada",
    "proyecto_id": 2
  }'
```

### Obtener Resumen de Proyecto
```bash
curl -X GET "http://localhost:8000/proyectos/1/resumen"
```

### Eliminar Proyecto
```bash
curl -X DELETE "http://localhost:8000/proyectos/1"
```

## ⚠️ Códigos de Error

| Código | Descripción                                    |
|--------|------------------------------------------------|
| 200    | Operación exitosa                              |
| 201    | Recurso creado exitosamente                    |
| 400    | Datos inválidos (ej: proyecto_id inexistente)  |
| 404    | Recurso no encontrado                          |
| 409    | Conflicto (ej: nombre de proyecto duplicado)   |
| 422    | Error de validación de datos                   |

## 🔍 Funcionalidades Implementadas

### Relaciones entre Tablas
- ✅ Relación 1:N entre proyectos y tareas
- ✅ Clave foránea con `ON DELETE CASCADE`
- ✅ Integridad referencial validada

### CRUD Completo
- ✅ Proyectos: Create, Read, Update, Delete
- ✅ Tareas: Create, Read, Update, Delete
- ✅ Validaciones con Pydantic

### Filtros Avanzados
- ✅ Búsqueda de proyectos por nombre
- ✅ Filtrar tareas por estado
- ✅ Filtrar tareas por prioridad
- ✅ Filtrar tareas por proyecto
- ✅ Combinación de múltiples filtros
- ✅ Ordenamiento ascendente/descendente

### Estadísticas
- ✅ Resumen por proyecto (tareas por estado y prioridad)
- ✅ Resumen general de la aplicación
- ✅ Proyecto con más tareas

### Validaciones
- ✅ Nombres únicos de proyectos
- ✅ Estados y prioridades válidas
- ✅ Campos obligatorios no vacíos
- ✅ Referencias válidas entre tablas

## 🧪 Ejecutar Tests

Para verificar que todo funciona correctamente:

```bash
pytest test_tp4.py -v
```

Esto ejecutará todos los tests y verificará:
- Estructura de la base de datos
- CRUD de proyectos y tareas
- Filtros y búsquedas
- Estadísticas y resúmenes
- Validaciones
- Integridad referencial

## 📂 Estructura del Proyecto

```
TP4/
├── main.py           # Aplicación FastAPI con todos los endpoints
├── models.py         # Modelos Pydantic para validación
├── database.py       # Funciones de acceso a la base de datos
├── tareas.db         # Base de datos SQLite (se crea automáticamente)
├── test_tp4.py       # Tests automatizados
└── README.md         # Archivo de documentacion del trabajo practico

### 🔐 Características de Seguridad

- **Validación de entrada:** Todos los datos son validados con Pydantic
- **SQL Injection:** Protección mediante consultas parametrizadas
- **Integridad referencial:** Claves foráneas con constraints
- **Manejo de errores:** Respuestas apropiadas para cada tipo de error

### 💡 Casos de Uso

### Caso 1: Crear Proyecto con Tareas
```bash
# 1. Crear proyecto
curl -X POST "http://localhost:8000/proyectos" \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Desarrollo Web"}'

# 2. Crear tareas
curl -X POST "http://localhost:8000/proyectos/1/tareas" \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Diseñar UI", "prioridad": "alta"}'

curl -X POST "http://localhost:8000/proyectos/1/tareas" \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Implementar backend", "prioridad": "media"}'
```

### Caso 2: Mover Tarea a Otro Proyecto
```bash
# Actualizar proyecto_id de la tarea
curl -X PUT "http://localhost:8000/tareas/1" \
  -H "Content-Type: application/json" \
  -d '{"proyecto_id": 2}'
```

### Caso 3: Ver Tareas Pendientes de Alta Prioridad
```bash
curl -X GET "http://localhost:8000/tareas?estado=pendiente&prioridad=alta"
```

### Caso 4: Eliminar Proyecto y Sus Tareas
```bash
# Al eliminar el proyecto, todas sus tareas se eliminan automáticamente (CASCADE)
curl -X DELETE "http://localhost:8000/proyectos/1"
```



