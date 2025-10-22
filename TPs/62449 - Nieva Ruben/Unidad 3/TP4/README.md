README.md – API de Tareas TP4

1️⃣ Descripción

Esta API permite gestionar proyectos y sus tareas asociadas usando SQLite como base de datos.
Se pueden crear, listar, actualizar y eliminar proyectos y tareas, aplicar filtros avanzados, y obtener resúmenes y estadísticas.


2️⃣ Requisitos

Python 3.9+

FastAPI

Uvicorn

SQLite3


Instalación rápida:

pip install fastapi uvicorn



3️⃣ Iniciar el servidor

uvicorn main:app --reload

La documentación automática estará disponible en:

http://127.0.0.1:8000/docs



4️⃣ Estructura de la base de datos

Tabla proyectos

Columna	Tipo	Restricción

id	INTEGER	PK, autoincrement
nombre	TEXT	NOT NULL, UNIQUE
descripcion	TEXT	Opcional
fecha_creacion	TEXT	NOT NULL


Tabla tareas

Columna	Tipo	Restricción

id	INTEGER	PK, autoincrement
descripcion	TEXT	NOT NULL
estado	TEXT	NOT NULL, valores: 'pendiente', 'en_progreso', 'completada'
prioridad	TEXT	NOT NULL, valores: 'baja', 'media', 'alta'
proyecto_id	INTEGER	FK → proyectos.id, ON DELETE CASCADE
fecha_creacion	TEXT	NOT NULL



5️⃣ Endpoints

Proyectos

Método	Ruta	Descripción

GET	/proyectos	Lista todos los proyectos
GET	/proyectos/{id}	Obtiene un proyecto específico
POST	/proyectos	Crea un nuevo proyecto
PUT	/proyectos/{id}	Modifica un proyecto existente
DELETE	/proyectos/{id}	Elimina un proyecto y sus tareas
GET	/proyectos/{id}/tareas	Lista todas las tareas de un proyecto
POST	/proyectos/{id}/tareas	Crea una tarea dentro de un proyecto
GET	/proyectos/{id}/resumen	Devuelve estadísticas del proyecto


Filtros disponibles en proyectos

/proyectos?nombre=parcial → Filtra por nombre que contenga texto.



Tareas

Método	Ruta	Descripción

GET	/tareas	Lista todas las tareas
PUT	/tareas/{id}	Modifica una tarea
DELETE	/tareas/{id}	Elimina una tarea


Filtros disponibles en tareas

/tareas?estado=pendiente → Filtra por estado

/tareas?prioridad=alta → Filtra por prioridad

/tareas?proyecto_id=1 → Filtra por proyecto

/tareas?estado=completada&prioridad=alta → Filtra combinando parámetros

/tareas?orden=asc o desc → Ordena por fecha de creación



Resumen general

Método	Ruta	Descripción

GET	/resumen	Resumen general de toda la aplicación




6️⃣ Ejemplos de requests

Crear proyecto

POST /proyectos
{
  "nombre": "Proyecto Alpha",
  "descripcion": "Primer proyecto de prueba"
}

Crear tarea dentro de proyecto

POST /proyectos/1/tareas
{
  "descripcion": "Estudiar FastAPI",
  "estado": "pendiente",
  "prioridad": "alta"
}

Filtrar tareas por estado y prioridad

GET /tareas?estado=pendiente&prioridad=alta

Obtener resumen de un proyecto

GET /proyectos/1/resumen

Ejemplo de respuesta:

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

Resumen general

GET /resumen

Ejemplo de respuesta:

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


7️⃣ Integridad referencial

Al eliminar un proyecto, se eliminan todas sus tareas automáticamente (ON DELETE CASCADE).

No se puede crear una tarea con un proyecto_id inexistente.

Se puede mover una tarea a otro proyecto modificando su proyecto_id.