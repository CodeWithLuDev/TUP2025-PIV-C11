🧩 Trabajo Práctico N°4 – Relaciones entre Tablas y Filtros Avanzados
📘 Descripción General

Este proyecto implementa una API REST con FastAPI y SQLite que gestiona Proyectos y Tareas con una relación 1:N (un proyecto puede tener muchas tareas).
Incluye operaciones CRUD completas, filtros avanzados, validaciones con Pydantic y endpoints de resumen estadístico.

🚀 Instrucciones para Ejecutar el Servidor
1️⃣ Requisitos previos

Python 3.9 o superior

Instalar dependencias necesarias:

pip install fastapi uvicorn pydantic

2️⃣ Inicializar la base de datos

La base se crea automáticamente al iniciar el servidor gracias a la función init_db() en main.py.

3️⃣ Ejecutar el servidor

Desde la carpeta del proyecto, correr:

uvicorn main:app --reload


Luego acceder a la documentación interactiva:

Swagger UI → http://127.0.0.1:8000/docs

Redoc → http://127.0.0.1:8000/redoc

📁 Estructura del Proyecto
TP4/
│
├── main.py          # Archivo principal con los endpoints
├── models.py        # Modelos Pydantic para validaciones
├── database.py      # Funciones auxiliares y conexión SQLite
├── tareas.db        # Base de datos SQLite (se genera automáticamente)
└── README.md        # Documentación del proyecto

🧱 Estructura de la Base de Datos
Tabla: proyectos
Campo	Tipo	Restricciones
id	INTEGER	PRIMARY KEY AUTOINCREMENT
nombre	TEXT	NOT NULL, UNIQUE
descripcion	TEXT	NULL
fecha_creacion	TEXT	NOT NULL
Tabla: tareas
Campo	Tipo	Restricciones
id	INTEGER	PRIMARY KEY AUTOINCREMENT
descripcion	TEXT	NOT NULL
estado	TEXT	NOT NULL
prioridad	TEXT	NOT NULL
proyecto_id	INTEGER	FOREIGN KEY (proyectos.id) ON DELETE CASCADE
fecha_creacion	TEXT	NOT NULL

📌 Relación:
Cada tarea pertenece a un proyecto mediante proyecto_id.
Si se elimina un proyecto, sus tareas también se eliminan automáticamente (ON DELETE CASCADE).

⚙️ Endpoints Principales
🔹 Proyectos
Método	Ruta	Descripción
GET	/proyectos	Lista todos los proyectos (permite buscar por nombre)
GET	/proyectos/{id}	Obtiene un proyecto específico
POST	/proyectos	Crea un nuevo proyecto
PUT	/proyectos/{id}	Modifica un proyecto existente
DELETE	/proyectos/{id}	Elimina un proyecto y sus tareas asociadas
GET	/proyectos/{id}/resumen	Devuelve estadísticas del proyecto

Ejemplo – Crear un proyecto

curl -X POST http://127.0.0.1:8000/proyectos \
     -H "Content-Type: application/json" \
     -d '{"nombre": "Proyecto Alpha", "descripcion": "Desarrollo web"}'


Ejemplo – Filtrar por nombre

GET /proyectos?nombre=Alpha

🔹 Tareas
Método	Ruta	Descripción
GET	/tareas	Lista todas las tareas (de todos los proyectos, con filtros)
GET	/proyectos/{id}/tareas	Lista las tareas de un proyecto específico
POST	/proyectos/{id}/tareas	Crea una tarea dentro de un proyecto
PUT	/tareas/{id}	Actualiza una tarea (puede cambiar de proyecto)
DELETE	/tareas/{id}	Elimina una tarea

Ejemplo – Crear una tarea

curl -X POST http://127.0.0.1:8000/proyectos/1/tareas \
     -H "Content-Type: application/json" \
     -d '{"descripcion": "Configurar entorno", "estado": "pendiente", "prioridad": "alta"}'


Ejemplo – Filtros disponibles

GET /tareas?estado=pendiente
GET /tareas?prioridad=alta
GET /tareas?estado=completada&prioridad=alta
GET /tareas?proyecto_id=2
GET /tareas?orden=asc

🔹 Resumenes y Estadísticas
Método	Ruta	Descripción
GET	/proyectos/{id}/resumen	Devuelve estadísticas de un proyecto
GET	/resumen	Devuelve un resumen general de la aplicación

Ejemplo – /proyectos/1/resumen

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


Ejemplo – /resumen

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

🧠 Validaciones y Manejo de Errores

Pydantic Models:

ProyectoCreate y ProyectoUpdate

TareaCreate y TareaUpdate

Errores controlados:

404 → Proyecto o tarea no encontrada

400 → Datos inválidos (ej: proyecto inexistente)

409 → Conflicto (nombre de proyecto duplicado)

🔗 Relaciones entre Tablas

Relación 1:N:
Un proyecto puede tener muchas tareas, pero una tarea pertenece a un solo proyecto.

Integridad referencial:
Si se elimina un proyecto, sus tareas se eliminan automáticamente (ON DELETE CASCADE).

Consultas JOIN:
Se usan JOINs para obtener información combinada (por ejemplo, el nombre del proyecto en cada tarea o el conteo de tareas por proyecto).

✅ Ejemplos de Pruebas Rápidas
# Crear un proyecto
curl -X POST http://127.0.0.1:8000/proyectos -H "Content-Type: application/json" -d '{"nombre": "Proyecto Beta"}'

# Listar proyectos
curl http://127.0.0.1:8000/proyectos

# Crear tarea en proyecto 1
curl -X POST http://127.0.0.1:8000/proyectos/1/tareas -H "Content-Type: application/json" -d '{"descripcion": "Diseñar logo", "estado": "pendiente", "prioridad": "media"}'

# Listar tareas de proyecto 1
curl http://127.0.0.1:8000/proyectos/1/tareas


✍️ Autor: Trabajo Práctico N°4 – Relaciones entre Tablas y Filtros Avanzados
📅 Materia: Programación Backend con Python y FastAPI