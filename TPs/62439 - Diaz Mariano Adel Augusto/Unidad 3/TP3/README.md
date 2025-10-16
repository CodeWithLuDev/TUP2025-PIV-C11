# 🧠 TP3 – API de Tareas Persistente (FastAPI + SQLite)

### Alumno: **Mariano Díaz Adel Augusto**

### Materia: **Programación IV**

### Profesor: *[Nombre del docente]*

### Fecha: **Octubre 2025**

-----

## 📘 Descripción general

Este proyecto implementa una **API RESTful** desarrollada con **FastAPI** que permite gestionar una lista de tareas (**CRUD**) de forma **persistente** utilizando una base de datos **SQLite**.

El sistema permite crear, listar, actualizar y eliminar tareas, así como aplicar filtros y generar un resumen de estados y prioridades.

A diferencia del TP anterior, los datos **se almacenan de forma permanente** en el archivo `tareas.db`.

-----

## ⚙️ Requisitos previos

Asegúrate de tener instalado **Python 3.10 o superior**.

Luego, instalá las dependencias necesarias con el siguiente comando:

```bash
pip install fastapi uvicorn pytest requests httpx
```

-----

## 🚀 Ejecución del servidor

Abrí una terminal en la carpeta del proyecto (`TP3/`).

Ejecutá el servidor con:

```bash
uvicorn main:app --reload
```

Abrí el navegador en:
👉 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

Ahí vas a encontrar la documentación interactiva **Swagger** generada automáticamente por FastAPI. Desde ahí podés probar cada *endpoint* sin usar Postman.

-----

## 🧱 Estructura del proyecto

```bash
TP3/
│
├── main.py           # Código principal de la API
├── test_TP3.py       # Archivo con los tests automáticos
├── TP3.md            # Enunciado del trabajo práctico
├── tareas.db         # Base de datos SQLite (se crea automáticamente)
└── README.md         # Este archivo (manual de usuario)
```

-----

## 🧩 Funcionalidades principales

### 📌 Endpoints CRUD

| Método | Ruta | Descripción |
| :---: | :--- | :--- |
| `GET` | `/tareas` | Lista todas las tareas almacenadas. |
| `POST` | `/tareas` | Crea una nueva tarea con validación automática. |
| `PUT` | `/tareas/{id}` | Modifica una tarea existente. |
| `DELETE` | `/tareas/{id}` | Elimina una tarea por su ID. |

### ✨ Filtros disponibles (Query Params)

| Parámetro | Ejemplo | Descripción |
| :---: | :---: | :--- |
| `estado` | `/tareas?estado=pendiente` | Filtra por estado. |
| `texto` | `/tareas?texto=comprar` | Busca texto dentro de la descripción. |
| `prioridad` | `/tareas?prioridad=alta` | Filtra por prioridad. |
| `orden` | `/tareas?orden=desc` | Ordena por fecha de creación (`asc` o `desc`). |

### 🧮 Endpoints adicionales (Mejoras obligatorias)

| Ruta | Método | Descripción |
| :--- | :---: | :--- |
| `/tareas/resumen` | `GET` | Devuelve un resumen con el total de tareas por estado y prioridad. |
| `/tareas/completar_todas` | `PUT` | Marca todas las tareas como completadas. |

-----

## 📄 Ejemplo de uso (JSON)

### ➕ Crear tarea

**Request**

```json
POST /tareas
{
  "descripcion": "Estudiar FastAPI",
  "estado": "pendiente",
  "prioridad": "alta"
}
```

**Response**

```json
{
  "id": 1,
  "descripcion": "Estudiar FastAPI",
  "estado": "pendiente",
  "fecha_creacion": "2025-10-16T14:25:33.245617",
  "prioridad": "alta"
}
```

-----

## 🧠 Validaciones automáticas

La API valida los datos de entrada usando **Pydantic**:

  * La **descripción** no puede estar vacía ni contener solo espacios.
  * Los estados válidos son: **"pendiente"**, **"en\_progreso"**, **"completada"**.
  * Las prioridades válidas son: **"baja"**, **"media"**, **"alta"**.

Si alguna validación falla, devuelve error **422 (Unprocessable Entity)** con el detalle del campo incorrecto.

-----

## 🧪 Ejecución de tests automáticos

Asegurate de tener el archivo `test_TP3.py` en la misma carpeta que `main.py`.

En la terminal, ejecutá:

```bash
pytest test_TP3.py -v
```

Deberías obtener algo como:

```diff
========================== test session starts ==========================
collected 30 items
test_TP3.py ................................. PASSED
========================== 30 passed in 1.2s ==========================
```

💡 Si aparece algún *warning*, no afecta el resultado del TP.

-----

## 🧰 Tecnología utilizada

  * **Lenguaje:** Python
  * **Framework:** FastAPI
  * **Base de datos:** SQLite
  * **Validación:** Pydantic
  * **Testing:** Pytest
  * **Servidor:** Uvicorn