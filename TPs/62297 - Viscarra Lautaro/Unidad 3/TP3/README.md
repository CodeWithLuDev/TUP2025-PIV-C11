API de Tareas Persistente
Descripción
API REST desarrollada con FastAPI para gestionar tareas con persistencia de datos en SQLite. Los datos se guardan en una base de datos y se mantienen entre reinicios de la aplicación.

Características
CRUD Completo: Crear, leer, actualizar y eliminar tareas
Persistencia: Datos almacenados en SQLite
Validaciones: Usando Pydantic Models
Filtros Avanzados: Por estado, prioridad y búsqueda de texto
Ordenamiento: Ascendente y descendente por fecha
Resumen: Estadísticas de tareas por estado y prioridad
Manejo de Errores: Respuestas HTTP apropiadas
Tecnologías Utilizadas
FastAPI: Framework web asincrónico
SQLite: Base de datos relacional
Pydantic: Validación de datos
Python 3.8+: Lenguaje de programación
Instalación
1. Clonar o descargar el proyecto
bash
cd TP3
2. Crear un entorno virtual (recomendado)
bash
python -m venv venv
Activar el entorno:
venv\Scripts\activate
3. Instalar dependencias
bash
pip install fastapi uvicorn pytest
Cómo iniciar el servidor
bash
uvicorn main:app --reload
El servidor estará disponible en: http://localhost:8000

Documentación interactiva: http://localhost:8000/docs (Swagger UI)

Estructura del Proyecto
TP3/
├── main.py              # API principal
├── tareas.db            # Base de datos SQLite (se crea automáticamente)
└── README.md            # Este archivo
Endpoints de la API
1. Información de la API
http
GET /
Respuesta:

json
{
  "nombre": "API de Tareas",
  "version": "1.0.0",
  "descripcion": "API para gestionar tareas con persistencia en SQLite",
  "endpoints": { ... }
}
2. Crear una tarea
http
POST /tareas
Content-Type: application/json

{
  "descripcion": "Comprar leche",
  "estado": "pendiente",
  "prioridad": "media"
}
Campos:

descripcion (string, requerido): Descripción de la tarea (no vacía)
estado (string, opcional): pendiente, en_progreso, completada (default: pendiente)
prioridad (string, opcional): baja, media, alta (default: media)
Respuesta (201 Created):

json
{
  "id": 1,
  "descripcion": "Comprar leche",
  "estado": "pendiente",
  "prioridad": "media",
  "fecha_creacion": "2025-10-17T14:30:45.123456"
}
Errores:

422: Descripción vacía, estado inválido o prioridad inválida
3. Obtener todas las tareas
http
GET /tareas
Respuesta (200 OK):

json
[
  {
    "id": 1,
    "descripcion": "Comprar leche",
    "estado": "pendiente",
    "prioridad": "media",
    "fecha_creacion": "2025-10-17T14:30:45.123456"
  },
  {
    "id": 2,
    "descripcion": "Estudiar Python",
    "estado": "en_progreso",
    "prioridad": "alta",
    "fecha_creacion": "2025-10-17T14:35:20.654321"
  }
]
4. Filtrar tareas por estado
http
GET /tareas?estado=pendiente
Valores válidos: pendiente, en_progreso, completada

Respuesta (200 OK): Array de tareas con el estado especificado

5. Buscar tareas por texto
http
GET /tareas?texto=comprar
Busca en la descripción de las tareas (case-insensitive)

Respuesta (200 OK): Array de tareas que contienen el texto

6. Filtrar tareas por prioridad
http
GET /tareas?prioridad=alta
Valores válidos: baja, media, alta

Respuesta (200 OK): Array de tareas con la prioridad especificada

7. Ordenar tareas por fecha
http
GET /tareas?orden=desc
Valores válidos:

desc: Más recientes primero
asc: Más antiguas primero (default)
Respuesta (200 OK): Array de tareas ordenadas

8. Combinar múltiples filtros
http
GET /tareas?estado=pendiente&prioridad=alta&texto=comprar&orden=desc
Todos los filtros son opcionales y se pueden combinar.

Respuesta (200 OK): Array de tareas que cumplen todos los criterios

9. Obtener resumen de tareas
http
GET /tareas/resumen
Respuesta (200 OK):

json
{
  "total_tareas": 5,
  "por_estado": {
    "pendiente": 2,
    "en_progreso": 1,
    "completada": 2
  },
  "por_prioridad": {
    "baja": 1,
    "media": 2,
    "alta": 2
  }
}
10. Actualizar una tarea
http
PUT /tareas/1
Content-Type: application/json

{
  "descripcion": "Comprar leche y pan",
  "estado": "en_progreso",
  "prioridad": "alta"
}
Respuesta (200 OK):

json
{
  "id": 1,
  "descripcion": "Comprar leche y pan",
  "estado": "en_progreso",
  "prioridad": "alta",
  "fecha_creacion": "2025-10-17T14:30:45.123456"
}
Errores:

404: Tarea no encontrada
422: Datos inválidos
11. Marcar todas las tareas como completadas
http
PUT /tareas/completar_todas
Respuesta (200 OK):

json
{
  "mensaje": "3 tareas marcadas como completadas"
}
12. Eliminar una tarea
http
DELETE /tareas/1
Respuesta (200 OK):

json
{
  "mensaje": "Tarea 1 eliminada correctamente"
}
Errores:

404: Tarea no encontrada
Ejemplos de Uso con cURL
Crear una tarea
bash
curl -X POST http://localhost:8000/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Tarea importante", "estado": "pendiente", "prioridad": "alta"}'
Obtener todas las tareas
bash
curl http://localhost:8000/tareas
Filtrar por estado
bash
curl http://localhost:8000/tareas?estado=completada
Buscar por texto
bash
curl http://localhost:8000/tareas?texto=python
Obtener resumen
bash
curl http://localhost:8000/tareas/resumen
Actualizar una tarea
bash
curl -X PUT http://localhost:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Tarea actualizada", "estado": "en_progreso"}'
Eliminar una tarea
bash
curl -X DELETE http://localhost:8000/tareas/1
Validaciones
La API valida automáticamente los datos usando Pydantic:

Campo	Validación
descripcion	No puede estar vacía, no solo espacios
estado	Debe ser: pendiente, en_progreso o completada
prioridad	Debe ser: baja, media o alta
Si los datos no son válidos, la API devuelve 422 Unprocessable Entity con detalles del error.

Base de Datos
Estructura de la tabla tareas
sql
CREATE TABLE tareas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    descripcion TEXT NOT NULL,
    estado TEXT NOT NULL,
    prioridad TEXT DEFAULT 'media',
    fecha_creacion TEXT NOT NULL
)
Columnas:

id: Identificador único (auto-incrementado)
descripcion: Texto de la tarea (obligatorio)
estado: Estado actual (obligatorio)
prioridad: Nivel de prioridad (opcional, default: 'media')
fecha_creacion: Timestamp ISO 8601 (obligatorio)
Persistencia
Los datos se guardan automáticamente en el archivo tareas.db. No se pierden al reiniciar la aplicación.

Testeo
Ejecutar todos los tests
bash
pytest test_TP3.py -v
Ejecutar un test específico
bash
pytest test_TP3.py::test_crear_tarea -v
Ejecutar con reporte de cobertura
bash
pytest test_TP3.py -v --cov=main
Total de tests: 27 tests unitarios

Códigos de Estado HTTP
Código	Significado
200	OK - Solicitud exitosa
201	Created - Recurso creado exitosamente
400	Bad Request - Solicitud inválida
404	Not Found - Recurso no encontrado
422	Unprocessable Entity - Datos inválidos (validación Pydantic)
500	Internal Server Error - Error del servidor
Notas Importantes
La base de datos tareas.db se crea automáticamente al iniciar la aplicación
Todos los datos son persistentes: Se guardan en SQLite
Las validaciones se realizan con Pydantic: Errores 422 indican datos inválidos
Los timestamps están en formato ISO 8601: Ejemplo: 2025-10-17T14:30:45.123456
Los filtros son case-insensitive: Buscar "Python" es igual a buscar "python"
Autor
Trabajo Práctico N°3 - Backend con FastAPI y SQLite

Fecha
Octubre 2025

