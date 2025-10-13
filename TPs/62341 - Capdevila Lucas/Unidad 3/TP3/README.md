# Mini API de Tareas - TP3

API REST para gestión de tareas con persistencia en SQLite, desarrollada con FastAPI.

## Características

- ✅ CRUD completo de tareas (Crear, Leer, Actualizar, Eliminar)
- ✅ Persistencia de datos en base de datos SQLite
- ✅ Filtros avanzados por estado, texto y prioridad
- ✅ Ordenamiento por fecha de creación
- ✅ Validación de datos con Pydantic
- ✅ Endpoint de resumen estadístico
- ✅ Operaciones en lote (completar todas las tareas)

## Instalación

1. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Ejecutar el servidor:**
   ```bash
   uvicorn main:app --reload
   ```

3. **Acceder a la documentación:**
   - API: http://127.0.0.1:8000/
   - Documentación interactiva: http://127.0.0.1:8000/docs
   - Documentación alternativa: http://127.0.0.1:8000/redoc

## Estructura de la Base de Datos

La aplicación crea automáticamente la base de datos `tareas.db` con la siguiente estructura:

```sql
CREATE TABLE tareas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    descripcion TEXT NOT NULL,
    estado TEXT NOT NULL,
    fecha_creacion TEXT,
    prioridad TEXT NOT NULL
);
```

## Endpoints de la API

### 1. Información de la API
```http
GET /
```

**Respuesta:**
```json
{
  "nombre": "Mini API de Tareas",
  "version": "1.0.0",
  "descripcion": "API REST para gestión de tareas con persistencia en SQLite",
  "endpoints": { ... }
}
```

### 2. Obtener todas las tareas
```http
GET /tareas
```

**Parámetros de consulta opcionales:**
- `estado`: Filtrar por estado (`pendiente`, `en_progreso`, `completada`)
- `texto`: Buscar texto en la descripción
- `prioridad`: Filtrar por prioridad (`baja`, `media`, `alta`)
- `orden`: Ordenar por fecha (`asc`, `desc`)

**Ejemplos:**
```bash
# Obtener todas las tareas
curl http://127.0.0.1:8000/tareas

# Filtrar por estado
curl "http://127.0.0.1:8000/tareas?estado=pendiente"

# Buscar texto
curl "http://127.0.0.1:8000/tareas?texto=comprar"

# Filtrar por prioridad alta
curl "http://127.0.0.1:8000/tareas?prioridad=alta"

# Ordenar por fecha descendente
curl "http://127.0.0.1:8000/tareas?orden=desc"

# Combinar filtros
curl "http://127.0.0.1:8000/tareas?estado=pendiente&prioridad=alta&orden=desc"
```

### 3. Crear nueva tarea
```http
POST /tareas
```

**Cuerpo de la petición:**
```json
{
  "descripcion": "Descripción de la tarea",
  "estado": "pendiente",        // Opcional: pendiente, en_progreso, completada
  "prioridad": "media"          // Opcional: baja, media, alta
}
```

**Ejemplo:**
```bash
curl -X POST http://127.0.0.1:8000/tareas \
  -H "Content-Type: application/json" \
  -d '{
    "descripcion": "Comprar leche",
    "estado": "pendiente",
    "prioridad": "alta"
  }'
```

### 4. Actualizar tarea existente
```http
PUT /tareas/{id}
```

**Cuerpo de la petición:**
```json
{
  "descripcion": "Nueva descripción",  // Opcional
  "estado": "completada",              // Opcional
  "prioridad": "baja"                  // Opcional
}
```

**Ejemplo:**
```bash
curl -X PUT http://127.0.0.1:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{
    "estado": "completada",
    "prioridad": "baja"
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

### 6. Resumen estadístico
```http
GET /tareas/resumen
```

**Respuesta:**
```json
{
  "total_tareas": 10,
  "por_estado": {
    "pendiente": 5,
    "en_progreso": 3,
    "completada": 2
  },
  "por_prioridad": {
    "alta": 2,
    "media": 6,
    "baja": 2
  }
}
```

### 7. Completar todas las tareas
```http
PUT /tareas/completar_todas
```

**Ejemplo:**
```bash
curl -X PUT http://127.0.0.1:8000/tareas/completar_todas
```

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
- La descripción no puede estar vacía
- Los estados y prioridades deben ser valores válidos
- Si no se especifica estado, se asigna `pendiente` por defecto
- Si no se especifica prioridad, se asigna `media` por defecto

## Códigos de respuesta HTTP

- `200 OK`: Operación exitosa
- `201 Created`: Tarea creada exitosamente
- `400 Bad Request`: Datos inválidos o filtros incorrectos
- `404 Not Found`: Tarea no encontrada
- `422 Unprocessable Entity`: Error de validación de Pydantic

## Persistencia de datos

Los datos se almacenan en la base de datos SQLite `tareas.db` que se crea automáticamente al iniciar la aplicación. Los datos persisten entre reinicios del servidor.

### Verificar persistencia

1. Crear algunas tareas:
   ```bash
   curl -X POST http://127.0.0.1:8000/tareas \
     -H "Content-Type: application/json" \
     -d '{"descripcion": "Tarea de prueba", "prioridad": "alta"}'
   ```

2. Detener el servidor (Ctrl+C)

3. Reiniciar el servidor:
   ```bash
   uvicorn main:app --reload
   ```

4. Verificar que las tareas siguen ahí:
   ```bash
   curl http://127.0.0.1:8000/tareas
   ```

## Ejemplos de uso con Python

```python
import requests

# Crear una tarea
response = requests.post("http://127.0.0.1:8000/tareas", json={
    "descripcion": "Estudiar Python",
    "estado": "pendiente",
    "prioridad": "alta"
})
print(response.json())

# Obtener todas las tareas
response = requests.get("http://127.0.0.1:8000/tareas")
tareas = response.json()
print(f"Total de tareas: {len(tareas)}")

# Filtrar tareas pendientes de alta prioridad
response = requests.get("http://127.0.0.1:8000/tareas?estado=pendiente&prioridad=alta")
tareas_urgentes = response.json()
print(f"Tareas urgentes: {len(tareas_urgentes)}")

# Obtener resumen
response = requests.get("http://127.0.0.1:8000/tareas/resumen")
resumen = response.json()
print(f"Resumen: {resumen}")
```

## Testing

### Ejecutar tests con pytest

```bash
# Opción 1: Usar el script personalizado (recomendado - sin errores)
python run_tests.py

# Opción 2: Tests sin errores de archivos (recomendado)
python -m pytest test_TP3_memory.py -v

# Opción 3: Tests originales (pueden mostrar errores de limpieza en Windows)
python -m pytest test_TP3.py -v

# Opción 4: Con configuración personalizada
python -m pytest test_TP3_memory.py -v --tb=short --disable-warnings
```

### Verificar funcionalidad específica

```bash
# Test individual - verificar base de datos (sin errores)
python -m pytest test_TP3_memory.py::test_base_datos_se_crea -v

# Test individual - verificar CRUD (sin errores)
python -m pytest test_TP3_memory.py::test_crear_tarea -v

# Test individual - verificar filtros (sin errores)
python -m pytest test_TP3_memory.py::test_filtro_por_estado -v

# Test individual - verificar resumen (sin errores)
python -m pytest test_TP3_memory.py::test_endpoint_resumen -v
```

**Nota:** Usa `test_TP3_memory.py` para evitar errores de `PermissionError` en Windows. Los tests originales (`test_TP3.py`) pueden mostrar errores de limpieza que no afectan la funcionalidad.

## Estructura del proyecto

```
TP3/
├── main.py              # Aplicación principal
├── test_TP3.py         # Tests automatizados (pueden mostrar errores de limpieza)
├── test_TP3_memory.py  # Tests sin errores de archivos (recomendado)
├── run_tests.py        # Script de testing mejorado
├── pytest.ini         # Configuración de pytest
├── requirements.txt    # Dependencias
├── README.md          # Este archivo
└── tareas.db          # Base de datos (se crea automáticamente)
```

## Tecnologías utilizadas

- **FastAPI**: Framework web moderno y rápido
- **SQLite**: Base de datos ligera y embebida
- **Pydantic**: Validación de datos y serialización
- **Uvicorn**: Servidor ASGI para FastAPI
