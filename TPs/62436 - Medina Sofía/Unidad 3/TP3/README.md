# API de Tareas Persistente - TP3
# DESCRIPCION
Esta es una API RESTful desarrollada con FastAPI que gestiona tareas con pertenencias en bases de datos SQLite. los datos se guardan de forma permanente en el archivo tareas.bd y no se pierden al reiniciar el servidor

# REQUISITOS
- Python 3.7
- FastAPI
- Uvicorn
- SQLite3 (incluido en python)

## Instalación

Primero, instalar las dependencias:
```bash
pip install fastapi uvicorn
```
## Cómo iniciar el servidor

Desde la carpeta TP3, ejecutar:
```bash
uvicorn main:app --reload
```

El servidor va a correr en `http://localhost:8000`

NOTA: la primera vez que se inicie el servidor se creara automaticamente el archivo tareas.db con la tabla de tareas.



## ENDPOINTS

### GET /
Devuelve información sobre la API y todos los endpoints disponibles.

Ejemplo de request:

```bash
curl http://localhost:8000/
```
Respuesta:

```json{
  "nombre": "API de Tareas Persistente",
  "version": "1.0",
  "endpoints": {
    "GET /tareas": "Obtener todas las tareas",
    "POST /tareas": "Crear una nueva tarea",
    "PUT /tareas/{id}": "Actualizar una tarea",
    "DELETE /tareas/{id}": "Eliminar una tarea",
    "GET /tareas/resumen": "Obtener resumen de tareas",
    "PUT /tareas/completar_todas": "Marcar todas las tareas como completadas"
  }
}
```


### 1. GET `/tareas`

Obtiene todas las tareas.

```bash
curl http://localhost:8000/tareas
```

Se puede filtrar por estado, texto, prioridad y ordenar:

```bash
# Filtrar por estado
curl http://localhost:8000/tareas?estado=pendiente

# Filtrar por prioridad
curl http://localhost:8000/tareas?prioridad=alta

# Buscar por texto
curl http://localhost:8000/tareas?texto=comprar

# Ordenar descendente
curl http://localhost:8000/tareas?orden=desc

# Combinar filtros
curl http://localhost:8000/tareas?estado=pendiente&prioridad=alta
```

Respuesta:
```json
[
  {
    "id": 1,
    "descripcion": "Comprar pan",
    "estado": "pendiente",
    "fecha_creacion": "2025-10-17 14:30:45.123456",
    "prioridad": "alta"
  }
]
```

### 2. POST `/tareas`

Crear una nueva tarea. La fecha de creacion de asigna automaticamente.

```bash
curl -X POST http://localhost:8000/tareas \
  -H "Content-Type: application/json" \
  -d '{
    "descripcion": "Comprar leche",
    "estado": "pendiente",
    "prioridad": "alta"
  }'
```

Por defecto, estado es "pendiente" y prioridad es "media", así que puedo omitirlos:

```bash
curl -X POST http://localhost:8000/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Tarea importante"}'
```

Respuesta:
```json
{
  "id": 1,
  "descripcion": "Comprar leche",
  "estado": "pendiente",
  "fecha_creacion": "2025-10-17 14:40:10.789123",
  "prioridad": "alta"
}
```

### 3. PUT `/tareas/{id}`

Actualizar una tarea.

```bash
curl -X PUT http://localhost:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{
    "descripcion": "Comprar leche desnatada",
    "estado": "completada",
    "prioridad": "media"
  }'
```

Respuesta:
```json
{
  "id": 1,
  "descripcion": "Comprar leche desnatada",
  "estado": "completada",
  "fecha_creacion": "2025-10-17 14:40:10.789123",
  "prioridad": "media"
}
```

### 4. DELETE `/tareas/{id}`

Eliminar una tarea.

```bash
curl -X DELETE http://localhost:8000/tareas/1
```

Respuesta:
```json
{
  "mensaje": "Tarea eliminada correctamente"
}
```

### 5. GET `/tareas/resumen`

Ver un resumen de las tareas.

```bash
curl http://localhost:8000/tareas/resumen
```

Respuesta:
```json
{
  "total_tareas": 4,
  "por_estado": {
    "pendiente": 2,
    "completada": 1,
    "en_progreso": 1
  },
  "por_prioridad": {
    "alta": 2,
    "baja": 1,
    "media": 1
  }
}
```

### 6. PUT `/tareas/completar_todas`

Marcar todas las tareas como completadas.

```bash
curl -X PUT http://localhost:8000/tareas/completar_todas
```

Respuesta:
```json
{
  "mensaje": "Todas las tareas han sido marcadas como completadas"
}
```

## VALIDACIONES

- La descripción no puede estar vacía
- El estado solo puede ser: pendiente, en_progreso, completada
- La prioridad solo puede ser: baja, media, alta

## BASE DE DATOS

Los datos se guardan en `tareas.db` y persisten cuando reinicio el servidor.

Para limpiar todo, simplemente eliminar el archivo `tareas.db` y reiniciar el servidor.

## Probar con Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Crear tarea
response = requests.post(f"{BASE_URL}/tareas", json={
    "descripcion": "Mi tarea",
    "estado": "pendiente",
    "prioridad": "alta"
})
print(response.json())

# Obtener todas
response = requests.get(f"{BASE_URL}/tareas")
print(response.json())

# Ver resumen
response = requests.get(f"{BASE_URL}/tareas/resumen")
print(response.json())
```