# API de Tareas

Una API RESTful construida con FastAPI para gestionar tareas con persistencia en SQLite. Permite crear, leer, actualizar y eliminar tareas con soporte para filtros, búsqueda y ordenamiento.

## 🚀 Características

- ✅ CRUD completo de tareas (Crear, Leer, Actualizar, Eliminar)
- ✅ Persistencia de datos con SQLite
- ✅ Validación de datos con Pydantic
- ✅ Filtros por estado, prioridad y texto
- ✅ Ordenamiento por fecha (ascendente/descendente)
- ✅ Resumen estadístico de tareas
- ✅ Operación para completar todas las tareas
- ✅ Tests completos con pytest

## 📋 Requisitos

- Python 3.8 o superior
- FastAPI
- Uvicorn
- Pytest
- Pydantic

## 🔧 Instalación

1. **Clonar o descargar el proyecto**

```bash
git clone <tu-repo>
cd tareas-api
```

2. **Crear un entorno virtual**

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. **Instalar dependencias**

```bash
pip install fastapi uvicorn pytest
```

## ▶️ Ejecutar la API

```bash
python main.py
```

La API estará disponible en `http://localhost:8000`

Accede a la documentación interactiva en:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 Tests

Ejecutar todos los tests:

```bash
pytest test_tp3.py -v
```

Ejecutar un test específico:

```bash
pytest test_tp3.py::test_crear_tarea -v
```

Ver cobertura:

```bash
pytest test_tp3.py --cov
```

## 📚 Endpoints

### Endpoint Raíz

**GET** `/`

Devuelve información general de la API.

```json
{
  "nombre": "API de Tareas",
  "version": "1.0",
  "endpoints": ["/tareas", "/tareas/resumen", "/tareas/completar_todas"]
}
```

### Tareas

#### Obtener todas las tareas

**GET** `/tareas`

Parámetros opcionales:
- `estado`: Filtrar por estado (pendiente, en_progreso, completada)
- `texto`: Buscar en la descripción
- `prioridad`: Filtrar por prioridad (baja, media, alta)
- `orden`: Ordenar por fecha (asc o desc)

```bash
# Obtener todas las tareas
GET /tareas

# Filtrar por estado
GET /tareas?estado=pendiente

# Buscar por texto
GET /tareas?texto=comprar

# Filtrar por prioridad
GET /tareas?prioridad=alta

# Combinar filtros
GET /tareas?estado=pendiente&prioridad=alta&texto=comprar&orden=desc
```

#### Crear una tarea

**POST** `/tareas`

```json
{
  "descripcion": "Comprar pan",
  "estado": "pendiente",
  "prioridad": "media"
}
```

Respuesta (201):
```json
{
  "id": 1,
  "descripcion": "Comprar pan",
  "estado": "pendiente",
  "fecha_creacion": "2025-10-17T10:30:00.000000",
  "prioridad": "media"
}
```

#### Actualizar una tarea

**PUT** `/tareas/{id}`

```json
{
  "descripcion": "Comprar pan integral",
  "estado": "completada",
  "prioridad": "alta"
}
```

#### Eliminar una tarea

**DELETE** `/tareas/{id}`

Respuesta (200):
```json
{
  "mensaje": "Tarea eliminada correctamente"
}
```

### Operaciones Especiales

#### Obtener resumen estadístico

**GET** `/tareas/resumen`

Devuelve un resumen con totales por estado y prioridad.

Respuesta:
```json
{
  "total_tareas": 4,
  "por_estado": {
    "pendiente": 2,
    "en_progreso": 1,
    "completada": 1
  },
  "por_prioridad": {
    "alta": 2,
    "media": 1,
    "baja": 1
  }
}
```

#### Completar todas las tareas

**PUT** `/tareas/completar_todas`

Marca todas las tareas como completadas.

Respuesta (200):
```json
{
  "mensaje": "Todas las tareas han sido completadas"
}
```

## 📊 Estructura de una Tarea

| Campo | Tipo | Descripción | Validación |
|-------|------|-------------|-----------|
| id | Integer | Identificador único | AUTO (PK) |
| descripcion | String | Descripción de la tarea | Requerido, no vacío |
| estado | String | Estado actual | pendiente, en_progreso, completada |
| fecha_creacion | String | Fecha de creación (ISO format) | AUTO |
| prioridad | String | Nivel de prioridad | baja, media, alta |

## 🗄️ Base de Datos

La API utiliza SQLite con una tabla `tareas`. La base de datos se crea automáticamente al ejecutar `init_db()`.

```sql
CREATE TABLE tareas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  descripcion TEXT NOT NULL,
  estado TEXT NOT NULL,
  fecha_creacion TEXT NOT NULL,
  prioridad TEXT NOT NULL DEFAULT 'media'
)
```

## ✅ Validaciones

- **Descripción**: No puede estar vacía ni contener solo espacios
- **Estado**: Solo acepta: `pendiente`, `en_progreso`, `completada`
- **Prioridad**: Solo acepta: `baja`, `media`, `alta`

Si falta algún campo requerido o hay un valor inválido, la API devuelve un error **422 Unprocessable Entity**.

## 📝 Ejemplos de Uso

### Con cURL

```bash
# Crear tarea
curl -X POST http://localhost:8000/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion":"Estudiar FastAPI","prioridad":"alta"}'

# Obtener todas
curl http://localhost:8000/tareas

# Filtrar por estado
curl "http://localhost:8000/tareas?estado=pendiente"

# Completar todas
curl -X PUT http://localhost:8000/tareas/completar_todas \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Con Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Crear tarea
response = requests.post(f"{BASE_URL}/tareas", json={
    "descripcion": "Comprar leche",
    "estado": "pendiente",
    "prioridad": "media"
})
print(response.json())

# Obtener todas
response = requests.get(f"{BASE_URL}/tareas")
tareas = response.json()

# Filtrar
response = requests.get(f"{BASE_URL}/tareas?estado=pendiente&prioridad=alta")
print(response.json())

# Completar todas
response = requests.put(f"{BASE_URL}/tareas/completar_todas", json={})
print(response.json())
```

## 🐛 Solución de Problemas

### Error 422 Unprocessable Entity

Esto significa que los datos enviados no cumplen con la validación. Verifica:
- Que todos los campos requeridos estén presentes
- Que los valores sean válidos (estado, prioridad, descripción no vacía)
- Que estés enviando JSON válido

### Error 404 Not Found

- Para actualizar/eliminar: La tarea con ese ID no existe
- Para endpoints: Verifica que la URL sea correcta

### La base de datos no se crea

Asegúrate de que:
- Tienes permisos de escritura en el directorio
- No hay conflictos de permisos en el archivo `tareas.db`

## 🏗️ Estructura del Proyecto

```
.
├── main.py           # Archivo principal con la API
├── test_tp3.py       # Tests de la API
├── tareas.db         # Base de datos SQLite (se crea automáticamente)
└── README.md         # Este archivo
```

## 📦 Tecnologías Utilizadas

- **FastAPI**: Framework web rápido y moderno
- **SQLite**: Base de datos ligera
- **Pydantic**: Validación de datos
- **Pytest**: Framework de testing
- **Uvicorn**: Servidor ASGI

## 📄 Licencia

Este proyecto está disponible bajo la licencia MIT.

## 👨‍💻 Autor

Creado como parte de un proyecto académico de Python y APIs REST.

---

**¿Preguntas?** Consulta la documentación interactiva en `/docs` cuando la API esté ejecutándose.