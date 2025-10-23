# API de Tareas Persistente - Trabajo Práctico N°3

## 📋 Descripción
API REST con persistencia en SQLite para gestionar tareas con operaciones CRUD completas, filtros avanzados, prioridades y ordenamiento.

## 🆕 Novedades del TP3

✅ **Persistencia con SQLite** - Los datos se guardan en `tareas.db`  
✅ **Campo de prioridad** - baja, media, alta  
✅ **Ordenamiento** - Por fecha de creación (asc/desc)  
✅ **Filtro por prioridad** - `GET /tareas?prioridad=alta`  
✅ **Base de datos automática** - Se crea al iniciar la aplicación  

## 🚀 Instalación

### 1. Crear entorno virtual (recomendado)
```bash
python -m venv venv
source venv/bin/activate  # En Linux/Mac
venv\Scripts\activate     # En Windows
```

### 2. Instalar dependencias
```bash
pip install fastapi uvicorn pydantic
```

### 3. Ejecutar la aplicación
```bash
uvicorn main:app --reload
```

La API estará disponible en: `http://127.0.0.1:8000`  
Documentación interactiva: `http://127.0.0.1:8000/docs`

## 🗄️ Base de Datos

La base de datos `tareas.db` se crea automáticamente al iniciar la aplicación.

### Estructura de la tabla `tareas`:

| Campo            | Tipo    | Descripción                           |
|------------------|---------|---------------------------------------|
| id               | INTEGER | Clave primaria (auto incremental)     |
| descripcion      | TEXT    | Descripción de la tarea (no nulo)     |
| estado           | TEXT    | pendiente, en_progreso o completada   |
| prioridad        | TEXT    | baja, media o alta (default: media)   |
| fecha_creacion   | TEXT    | Fecha y hora en formato ISO 8601      |

## 📚 Endpoints Disponibles

### 1. Obtener todas las tareas
```http
GET /tareas
```

**Query Params opcionales:**
- `estado`: `pendiente`, `en_progreso`, `completada`
- `texto`: buscar en descripción
- `prioridad`: `baja`, `media`, `alta`
- `orden`: `asc` o `desc` (por fecha de creación)

**Ejemplos:**
```bash
# Todas las tareas
curl http://127.0.0.1:8000/tareas

# Filtrar por estado
curl http://127.0.0.1:8000/tareas?estado=pendiente

# Buscar por texto
curl http://127.0.0.1:8000/tareas?texto=estudiar

# Filtrar por prioridad
curl http://127.0.0.1:8000/tareas?prioridad=alta

# Ordenar por fecha descendente
curl http://127.0.0.1:8000/tareas?orden=desc

# Combinar filtros
curl "http://127.0.0.1:8000/tareas?estado=pendiente&prioridad=alta&orden=desc"
```

### 2. Crear nueva tarea
```http
POST /tareas
```

**Body (JSON):**
```json
{
  "descripcion": "Completar el TP3",
  "estado": "pendiente",
  "prioridad": "alta"
}
```

**Ejemplo:**
```bash
curl -X POST http://127.0.0.1:8000/tareas \
  -H "Content-Type: application/json" \
  -d '{
    "descripcion": "Estudiar FastAPI y SQLite",
    "estado": "pendiente",
    "prioridad": "alta"
  }'
```

**Valores por defecto:**
- `estado`: `"pendiente"` (si no se especifica)
- `prioridad`: `"media"` (si no se especifica)

### 3. Obtener tarea específica
```http
GET /tareas/{id}
```

**Ejemplo:**
```bash
curl http://127.0.0.1:8000/tareas/1
```

### 4. Actualizar tarea
```http
PUT /tareas/{id}
```

**Body (JSON) - todos los campos son opcionales:**
```json
{
  "descripcion": "Descripción actualizada",
  "estado": "completada",
  "prioridad": "baja"
}
```

**Ejemplos:**
```bash
# Actualizar solo el estado
curl -X PUT http://127.0.0.1:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{"estado": "completada"}'

# Actualizar descripción y prioridad
curl -X PUT http://127.0.0.1:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{
    "descripcion": "Nueva descripción",
    "prioridad": "alta"
  }'
```

### 5. Eliminar tarea
```http
DELETE /tareas/{id}
```

**Ejemplo:**
```bash
curl -X DELETE http://127.0.0.1:8000/tareas/1
```

### 6. Obtener resumen de tareas
```http
GET /tareas/resumen
```

**Respuesta:**
```json
{
  "pendiente": 3,
  "en_progreso": 2,
  "completada": 5
}
```

**Ejemplo:**
```bash
curl http://127.0.0.1:8000/tareas/resumen
```

### 7. Completar todas las tareas
```http
PUT /tareas/completar_todas
```

**Respuesta:**
```json
{
  "mensaje": "Se completaron 5 tareas",
  "tareas_actualizadas": 5
}
```

**Ejemplo:**
```bash
curl -X PUT http://127.0.0.1:8000/tareas/completar_todas
```

## ✅ Características Implementadas

- ✅ **Persistencia con SQLite**
- ✅ CRUD completo (Create, Read, Update, Delete)
- ✅ Filtros por estado, texto y prioridad
- ✅ Ordenamiento por fecha (asc/desc)
- ✅ Validación de datos de entrada
- ✅ Códigos HTTP apropiados (200, 201, 400, 404)
- ✅ Mensajes de error en JSON
- ✅ Fecha de creación automática
- ✅ Resumen de tareas por estado
- ✅ Campo de prioridad (baja, media, alta)
- ✅ Completar todas las tareas
- ✅ Base de datos se crea automáticamente
- ✅ Context manager para conexiones seguras

## 🔍 Estados Válidos

- `pendiente`
- `en_progreso`
- `completada`

## 🎯 Prioridades Válidas

- `baja`
- `media` (valor por defecto)
- `alta`

## 📝 Estructura de una Tarea

```json
{
  "id": 1,
  "descripcion": "Completar el TP3",
  "estado": "en_progreso",
  "prioridad": "alta",
  "fecha_creacion": "2025-10-16T15:30:00.123456"
}
```

## ⚠️ Manejo de Errores

### Tarea no encontrada (404)
```json
{
  "detail": {
    "error": "La tarea no existe"
  }
}
```

### Descripción vacía (422)
```json
{
  "detail": [
    {
      "loc": ["body", "descripcion"],
      "msg": "La descripcion no puede estar vacia",
      "type": "value_error"
    }
  ]
}
```

### Estado inválido (400)
```json
{
  "error": "Estado 'invalido' no valido. Debe ser: pendiente, en_progreso o completada"
}
```

### Prioridad inválida (400)
```json
{
  "error": "Prioridad 'invalida' no valida. Debe ser: baja, media o alta"
}
```

## 🧪 Verificación de Persistencia

Para verificar que los datos persisten:

1. **Crear algunas tareas:**
```bash
curl -X POST http://127.0.0.1:8000/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Tarea 1", "prioridad": "alta"}'
```

2. **Detener el servidor** (Ctrl+C)

3. **Iniciar el servidor nuevamente:**
```bash
uvicorn main:app --reload
```

4. **Verificar que las tareas siguen ahí:**
```bash
curl http://127.0.0.1:8000/tareas
```

✅ **Las tareas deben aparecer** porque están guardadas en `tareas.db`

## 📦 Estructura del Proyecto

```
TP3/
│
├── main.py              # Aplicación FastAPI con SQLite
├── tareas.db           # Base de datos SQLite (se crea automáticamente)
├── README.md           # Este archivo
└── requirements.txt    # Dependencias (opcional)
```

## 🔧 Testeo

Para ejecutar los tests del profesor:

```bash
# Instalar pytest
pip install pytest httpx

# Ejecutar todos los tests
pytest test_TP3.py -v

# Ejecutar un test específico
pytest test_TP3.py::test_nombre_del_test -v
```

## 💾 Acceso directo a SQLite

Si quieres consultar la base de datos directamente:

```bash
# Abrir SQLite
sqlite3 tareas.db

# Ver la estructura de la tabla
.schema tareas

# Ver todas las tareas
SELECT * FROM tareas;

# Salir
.exit
```

## 🎓 Conceptos Aprendidos

- ✅ Conexión de FastAPI con SQLite
- ✅ Creación de tablas con SQL
- ✅ Sentencias INSERT, SELECT, UPDATE, DELETE
- ✅ Consultas SQL con filtros (WHERE, LIKE)
- ✅ Ordenamiento (ORDER BY)
- ✅ Agregaciones (COUNT, GROUP BY)
- ✅ Context managers para gestión de conexiones
- ✅ Conversión de resultados SQL a JSON
- ✅ Persistencia de datos

## 📚 Recursos

- [Documentación FastAPI](https://fastapi.tiangolo.com)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [Python sqlite3](https://docs.python.org/3/library/sqlite3.html)

---

**Autor**: Trabajo Práctico N°3 - FastAPI + SQLite  
**Fecha**: Octubre 2025  
**Entrega**: 17 de Octubre 2025 - 21:00hs