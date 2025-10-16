# Trabajo Práctico N°3 – API de Tareas Persistente (Persistencia con SQLite)

## Objetivos de Aprendizaje

- Conectar una API desarrollada con FastAPI a una base de datos SQLite.
- Crear tablas y almacenar datos de forma persistente (que no se pierdan al reiniciar el servidor).
- Consultar, insertar, modificar y eliminar datos usando sentencias SQL.
- Convertir los resultados de consultas en respuestas JSON para el cliente.

## Contexto

En el TP2 construiste una API que manejaba una lista de tareas en memoria (se borraban al reiniciar el servidor).
En este TP, vas a mejorar esa API para que los datos se guarden en una base de datos SQLite, logrando persistencia real.

Esto marca un paso clave: pasar de un CRUD “temporal” a uno persistente, que simula el funcionamiento de un sistema productivo.

## Enunciado Práctico

## 1. Migración a base de datos SQLite

- Crear una base de datos llamada **tareas.db**.
- Crear una tabla tareas con las siguientes columnas:

```SQL
id (entero, clave primaria, auto incremental),
descripcion (string, no acepta valores nulos),
estado (string, no acepta valores nulos),
fecha_creacion (string)
```

- Si la tabla no existe, debe crearse automáticamente al iniciar la aplicación (migración inicial).

> **Sugerencia**: crear una función `init_db()` que verifique y cree la tabla al iniciar el servidor.

## 2. CRUD persistente de tareas

Reutilizá los mismos endpoints del TP2, pero ahora deben leer y escribir en la base de datos.

| Método     | Ruta           | Descripción                            |
| ---------- | -------------- | -------------------------------------- |
| **GET**    | `/tareas`      | Devuelve todas las tareas desde la DB. |
| **POST**   | `/tareas`      | Inserta una nueva tarea.               |
| **PUT**    | `/tareas/{id}` | Modifica una tarea existente.          |
| **DELETE** | `/tareas/{id}` | Elimina una tarea existente.           |

**Requisitos funcionales:**

- Al crear una tarea (`POST`), validar que la descripción no esté vacía.
- Guardar la fecha y hora actual en el campo `fecha_creacion`.
- Solo aceptar los estados `"pendiente"`, `"en_progreso"` o `"completada"`.
- Manejar correctamente los errores (por ejemplo, intentar modificar una tarea inexistente debe devolver 404).

## 3. Búsquedas y filtros con Query Params

Implementar las mismas búsquedas del TP2, pero ahora usando consultas SQL:

- `GET /tareas?estado=pendiente` → devuelve solo las tareas con ese estado.
- `GET /tareas?texto=algo` → devuelve tareas cuya descripción contenga esa palabra.

## 4. Verificación de persistencia

- Probar crear algunas tareas, detener el servidor y volver a iniciarlo.
- Verificar que los datos se mantengan almacenados en `tareas.db`.

## 5. Implementación de Mejoras (obligatorio)

Agregá estas mejoras:

- **Endpoint de resumen**: `GET /tareas/resumen` que devuelva cuántas tareas hay por estado.
- **Campo “prioridad” (baja, media, alta)** y filtro adicional:
`GET /tareas?prioridad=alta`
- **Ordenamiento por fecha de creación:**
`GET /tareas?orden=desc` o `asc`.
- **Uso de Pydantic Models** para validar los datos que llegan en el body.

## Entregable

Subir dentro de la carpeta `TP3`:

- `main.py` (archivo principal de la API).
- `tareas.db` (base de datos creada por la aplicación).
- `README.md` explicando cómo iniciar el servidor, cómo acceder a los endpoints y ejemplos de requests.

El proyecto debe poder ejecutarse con:

```bash
uvicorn main:app --reload
```

## Fecha de entrega

**[IMPORTANTE]**

El trabajo debe presentarse hasta el 17 de OCTUBRE de 2025 a las 21:00hs.

---
---

## Testeo del práctico

1. **Instalar dependencias**:

    Instala las dependencias requeridas (si no la instalaron en los TPs anteriories):

    ```bash
    pip install pytest requests httpx # Instala las librerias en el entorno
    ```

2. **Verificar la estructura del proyecto**:

    Asegúrate de que el archivo con los tests (por ejemplo, test_TP3.py) y el archivo main.py (que contiene la aplicación FastAPI) estén en el mismo directorio o en una estructura accesible.

3. **Ejecutar los tests**

    - **Abrir una terminal**: Navega al directorio donde están los archivos test_TP3.py y main.py.
    - **Ejecutar pytest**: Usa el comando

        ```bash
        pytest test_TP3.py -v
        ```

    - -v habilita el modo verboso para ver detalles de cada prueba.
    - Esto ejecutará todos los tests definidos en el archivo (test_01 a test_27).

4. **Opcional: Ejecutar un test específico**:

    Si quieres ejecutar un solo test, por ejemplo, test_07_crear_tarea_exitosamente, usa:

    ```bash
    pytest test_TP3.py::test_00_nombre_del_test -v
    ```

5. **Verificar los resultados**

    **Salida esperada**: pytest mostrará un resumen de los tests ejecutados, indicando cuántos pasaron, fallaron o fueron omitidos.

    Ejemplo de salida exitosa

    ```bash
    ============================= test session starts =============================
    test_TP3... PASSED
    test_TP3... PASSED
    ...
    test_TP3... PASSED
    ============================= 20 passed in 0.12s ==============================
    ```

    - Si algún test falla, revisa el mensaje de error para identificar el problema (por ejemplo, un endpoint mal implementado en main.py o un problema con las aserciones).
