# TP3 - API de Tareas Persistente con SQLite

## Descripción
API REST desarrollada con FastAPI que gestiona tareas con persistencia en base de datos SQLite. Las tareas se mantienen almacenadas incluso después de reiniciar el servidor.

## Características
- ✅ CRUD completo de tareas (Crear, Leer, Actualizar, Eliminar)
- ✅ Persistencia con SQLite
- ✅ Validaciones con Pydantic
- ✅ Filtros por estado, texto y prioridad
- ✅ Ordenamiento por fecha de creación
- ✅ Resumen de tareas por estado
- ✅ Campo de prioridad (baja, media, alta)

## Requisitos
- Python 3.8+
- FastAPI
- Uvicorn

## Instalación

### 1. Instalar dependencias
```bash
pip install fastapi uvicorn pydantic
```

### 2. Iniciar el servidor
```bash
uvicorn main:app --reload
```

El servidor estará disponible en: `http://127.0.0.1:8000`

### 3. Documentación interactiva
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Endpoints

### 1. Obtener todas las tareas
**GET** `/tareas`

**Query Parameters opcionales:**
- `estado`: Filtrar por estado (`pendiente`, `en_progreso`, `completada`)
- `texto`: Buscar por texto en la descripción
- `prioridad`: Filtrar por prioridad (`baja`, `media`, `alta`)
- `orden`: Ordenar por fecha (`asc` o `desc`)

**Ejemplos:**
```bash
# Obtener todas las tareas
curl http://127.0.0.1:8000/tareas

# Filtrar por estado
curl http://127.0.0.1:8000/tareas?estado=pendiente

# Buscar por texto
curl http://127.0.0.1:8000/tareas?texto=comprar

# Filtrar por prioridad
curl http://127.0.0.1:8000/tareas?prioridad=alta

# Ordenar por fecha descendente
curl http://127.0.0.1:8000/tareas?orden=desc

# Combinar filtros
curl "http://127.0.0.1:8000/tareas?estado=pendiente&prioridad=alta&orden=desc"
```

### 2. Crear una tarea
**POST** `/tareas`

**Body (JSON):**
```json
{
  "descripcion": "Comprar leche",
  "estado": "pendiente",
  "prioridad": "media"
}
```

**Ejemplo con curl:**
```bash
curl -X POST http://127.0.0.1:8000/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Comprar leche", "estado": "pendiente", "prioridad": "alta"}'
```

**Respuesta:**
```json
{
  "id": 1,
  "descripcion": "Comprar leche",
  "estado": "pendiente",
  "prioridad": "alta",
  "fecha_creacion": "2025-10-17T15:30:00.123456"
}
```

### 3. Actualizar una tarea
**PUT** `/tareas/{id}`

**Body (JSON):**
```json
{
  "descripcion": "Comprar leche y pan",
  "estado": "completada",
  "prioridad": "baja"
}
```

**Ejemplo con curl:**
```bash
curl -X PUT http://127.0.0.1:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{"estado": "completada"}'
```

### 4. Eliminar una tarea
**DELETE** `/tareas/{id}`

**Ejemplo con curl:**
```bash
curl -X DELETE http://127.0.0.1:8000/tareas/1
```

**Respuesta:**
```json
{
  "mensaje": "Tarea eliminada correctamente"
}
```

### 5. Obtener resumen de tareas
**GET** `/tareas/resumen`

**Ejemplo:**
```bash
curl http://127.0.0.1:8000/tareas/resumen
```

**Respuesta:**
```json
{
  "pendiente": 5,
  "en_progreso": 2,
  "completada": 8
}
```

### 6. Completar todas las tareas
**PUT** `/tareas/completar_todas`

**Ejemplo:**
```bash
curl -X PUT http://127.0.0.1:8000/tareas/completar_todas
```

**Respuesta:**
```json
{
  "mensaje": "Todas las 15 tareas marcadas como completadas"
}
```

## Estados válidos
- `pendiente`
- `en_progreso`
- `completada`

## Prioridades válidas
- `baja`
- `media`
- `alta`

## Validaciones
- La descripción no puede estar vacía ni contener solo espacios
- El estado debe ser uno de los valores válidos
- La prioridad debe ser uno de los valores válidos
- Al intentar modificar o eliminar una tarea inexistente, se devuelve error 404

## Base de datos
El archivo `tareas.db` se crea automáticamente en el mismo directorio del proyecto al iniciar el servidor por primera vez.

## Verificación de persistencia
Para verificar que los datos persisten:

1. Crear algunas tareas usando POST
2. Detener el servidor (Ctrl+C)
3. Reiniciar el servidor con `uvicorn main:app --reload`
4. Hacer GET a `/tareas` y verificar que las tareas siguen allí

## Testing

### Instalar dependencias de testing
```bash
pip install pytest requests httpx
```

### Ejecutar tests
```bash
# Todos los tests
pytest test_TP3.py -v

# Un test específico
pytest test_TP3.py::test_00_nombre_del_test -v
```

## Estructura del proyecto
```
TP3/
├── main.py          # Archivo principal de la API
├── tareas.db        # Base de datos SQLite (se crea automáticamente)
├── README.md        # Este archivo
└── test_TP3.py      # Tests (provisto por la cátedra)
```

## Autor
[Tu nombre]

## Fecha de entrega
17 de Octubre de 2025 - 21:00hs