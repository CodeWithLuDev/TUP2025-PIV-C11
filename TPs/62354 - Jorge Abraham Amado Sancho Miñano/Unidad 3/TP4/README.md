# TP4 - Proyectos y Tareas (FastAPI + SQLite)

Este proyecto implementa una API REST para gestionar proyectos y tareas relacionadas (relación 1:N) usando SQLite y FastAPI. Está pensada para pasar la batería de tests proporcionada.

## Archivos principales
- main.py        : API (endpoints)
- models.py      : Modelos Pydantic para validación
- database.py    : Inicialización y conexión SQLite (DB_NAME = tareas.db)
- tareas.db      : Archivo de base de datos (se crea automáticamente)
- tests/         : Aquí van los tests (pytest)

## Requisitos
- Python 3.10+
- pip

## Instalación y ejecución local (VS Code)
1. Abrir la carpeta del proyecto en VS Code.
2. Abrir terminal integrada.

Crear y activar un entorno virtual (recomendado):
- macOS / Linux:
  python3 -m venv .venv
  source .venv/bin/activate
- Windows (PowerShell):
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1

Instalar dependencias:
pip install fastapi uvicorn pytest httpx

Ejecutar el servidor:
uvicorn main:app --reload

Los endpoints quedarán disponibles en http://127.0.0.1:8000

## Ejecutar tests (pytest)
En la terminal (con el virtualenv activado):
pytest -q

El test suite usa `init_db()` y el archivo `tareas.db` en la carpeta del proyecto. Los fixtures de los tests eliminan y crean la DB automáticamente antes de cada test.

## Endpoints principales (ejemplos)

- POST /proyectos
  Body:
  {
    "nombre": "Proyecto Alpha",
    "descripcion": "Opcional"
  }

- GET /proyectos
  - Soporta ?nombre=parcial para búsqueda por nombre.

- GET /proyectos/{id}
  - Devuelve proyecto e incluye "total_tareas".

- PUT /proyectos/{id}
  Body (parcial o completo)
  {
    "nombre": "Nuevo nombre",
    "descripcion": "Nueva descripción"
  }

- DELETE /proyectos/{id}
  - Devuelve {"message": "...", "tareas_eliminadas": N}

- POST /proyectos/{id}/tareas
  Body:
  {
    "descripcion": "Tarea X",
    "estado": "pendiente" (opcional),
    "prioridad": "media" (opcional)
  }

- GET /proyectos/{id}/tareas
  - Soporta filtros ?estado=&prioridad=&orden=asc|desc

- GET /tareas
  - Soporta filtros combinados: ?estado=&prioridad=&proyecto_id=&orden=

- PUT /tareas/{id}
  - Permite mover tarea cambiando proyecto_id y/o actualizar campos.

- GET /proyectos/{id}/resumen
  - Devuelve estadísticas por estado y prioridad para un proyecto.

- GET /resumen
  - Resumen general de la aplicación.

## Notas técnicas
- Las claves foráneas están definidas con `ON DELETE CASCADE`.
- Se habilitan `PRAGMA foreign_keys = ON` en cada conexión.
- Validación de datos con Pydantic (422 si payload inválido).
- Respuestas de error en español:
  - 404: no encontrado
  - 400: datos inválidos (por ejemplo proyecto_id inexistente)
  - 409: conflicto (nombre de proyecto duplicado)

```