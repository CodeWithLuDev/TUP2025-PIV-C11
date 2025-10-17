# TP3 - API de Tareas Persistente 📝

## Información General

| Campo | Valor |
| :--- | :--- |
| **Autor** | Francisco Javier Castro |
| **Tecnología** | **FastAPI** + **SQLite** |
| **Objetivo** | Implementar una **API REST** para la gestión de tareas con persistencia de datos en **SQLite**. |
| **Base de Datos** | `tareas.db` (se crea automáticamente al iniciar el servidor) |

---

## 1. Requisitos 🛠️

Para ejecutar el proyecto, necesitarás:

* **Python 3.10** o superior.
* `pip` (Administrador de paquetes de Python).
* Un navegador o una herramienta como **Postman** o `curl` para probar los *endpoints*.

---

## 2. Instalación y Ejecución ▶️

Sigue estos pasos para poner en marcha el servidor de la API:

### 2.1. Configuración Inicial

1.  Clona o descarga el proyecto:
    ```bash
    git clone <URL_DEL_PROYECTO>
    cd <CARPETA_DEL_PROYECTO>
    ```

2.  Crea y activa un entorno virtual (opcional, pero **muy recomendado**):

    ```bash
    python -m venv venv
    ```

    * **Windows:**
        ```bash
        venv\Scripts\activate
        ```
    * **Linux/macOS:**
        ```bash
        source venv/bin/activate
        ```

3.  Instala las dependencias necesarias:
    ```bash
    pip install fastapi uvicorn
    ```

### 2.2. Iniciar el Servidor

1.  Inicia el servidor con `uvicorn`. La opción `--reload` permite que los cambios en el código se reflejen sin reiniciar manualmente:
    ```bash
    uvicorn main:app --reload
    ```

2.  El servidor estará disponible en la siguiente dirección:
    [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 3. Endpoints Disponibles 🌐

La API expone los siguientes *endpoints* para la gestión de tareas.

### 3.1. Raíz de la API

| Método | Endpoint | Descripción |
| :--- | :--- | :--- |
| **GET** | `/` | Devuelve metadatos de la API (nombre, autor, versión y *endpoints* principales). |

**Respuesta Ejemplo:**
```json
{
  "nombre": "API de Tareas Persistente - TP3",
  "autor": "Francisco Javier Castro",
  "version": "1.0",
  "endpoints": [
    "/tareas",
    "/tareas/resumen",
    "/tareas/completar_todas"
  ]
}
3.2. Gestión de Tareas (/tareas)GET /tareasObtiene todas las tareas. Acepta parámetros de consulta para filtrado y ordenamiento.Parámetro (Query)Valores VálidosDescripciónestadopendiente, en_progreso, completadaFiltra por el estado de la tarea.prioridadbaja, media, altaFiltra por la prioridad de la tarea.textoCualquier stringBúsqueda por descripción (coincidencia parcial).ordenasc o descOrdena por id de forma ascendente o descendente.Ejemplo: Listar tareas pendientes ordenadas por ID ascendente.Bashcurl -X GET "[http://127.0.0.1:8000/tareas?estado=pendiente&orden=asc](http://127.0.0.1:8000/tareas?estado=pendiente&orden=asc)"
POST /tareasCrea una nueva tarea.Campo (Body - JSON)TipoValores VálidosObligatoriodescripcionstringCualquier stringSíestadostringpendiente, en_progreso, completadaSíprioridadstringbaja, media, altaSíEjemplo curl:Bashcurl -X POST "[http://127.0.0.1:8000/tareas](http://127.0.0.1:8000/tareas)" \
-H "Content-Type: application/json" \
-d "{\"descripcion\": \"Comprar pan\", \"estado\": \"pendiente\", \"prioridad\": \"media\"}"
PUT /tareas/{id}Modifica una tarea existente por su ID.Ejemplo curl:Bashcurl -X PUT "[http://127.0.0.1:8000/tareas/1](http://127.0.0.1:8000/tareas/1)" \
-H "Content-Type: application/json" \
-d "{\"descripcion\": \"Comprar leche\", \"estado\": \"completada\", \"prioridad\": \"alta\"}"
DELETE /tareas/{id}Elimina una tarea por su ID.Ejemplo curl:Bashcurl -X DELETE "[http://127.0.0.1:8000/tareas/1](http://127.0.0.1:8000/tareas/1)"
3.3. Operaciones AdicionalesPUT /tareas/completar_todasMarca todas las tareas como completada. No requiere cuerpo (body).Ejemplo curl:Bashcurl -X PUT "[http://127.0.0.1:8000/tareas/completar_todas](http://127.0.0.1:8000/tareas/completar_todas)"
Respuesta Ejemplo:JSON{
  "mensaje": "Todas las tareas fueron marcadas como completadas"
}
GET /tareas/resumenDevuelve un resumen de las tareas con conteos por estado y por prioridad.Ejemplo curl:Bashcurl -X GET "[http://127.0.0.1:8000/tareas/resumen](http://127.0.0.1:8000/tareas/resumen)"
Respuesta Ejemplo:JSON{
  "por_estado": {
    "pendiente": 2,
    "en_progreso": 1,
    "completada": 3
  },
  "por_prioridad": {
    "baja": 1,
    "media": 2,
    "alta": 3
  },
  "total_tareas": 6
}
4. Campos Válidos y Errores ⚠️CampoValores Válidosestado"pendiente", "en_progreso", "completada"prioridad"baja", "media", "alta"Nota: Si se intenta crear o modificar una tarea con valores inválidos para estado o prioridad, la API devolverá un error 422 Unprocessable Entity.5. Flujo de Ejemplo (curl) 🧪Aquí se muestra una secuencia rápida de comandos para probar la API:Crear tareas:Bashcurl -X POST "[http://127.0.0.1:8000/tareas](http://127.0.0.1:8000/tareas)" -H "Content-Type: application/json" -d "{\"descripcion\": \"Tarea 1\", \"estado\": \"pendiente\", \"prioridad\": \"alta\"}"
curl -X POST "[http://127.0.0.1:8000/tareas](http://127.0.0.1:8000/tareas)" -H "Content-Type: application/json" -d "{\"descripcion\": \"Tarea 2\", \"estado\": \"en_progreso\", \"prioridad\": \"media\"}"
Listar todas las tareas:Bashcurl -X GET "[http://127.0.0.1:8000/tareas](http://127.0.0.1:8000/tareas)"
Marcar todas como completadas:Bashcurl -X PUT "[http://127.0.0.1:8000/tareas/completar_todas](http://127.0.0.1:8000/tareas/completar_todas)"
Ver el resumen:Bashcurl -X GET "[http://127.0.0.1:8000/tareas/resumen](http://127.0.0.1:8000/tareas/resumen)"