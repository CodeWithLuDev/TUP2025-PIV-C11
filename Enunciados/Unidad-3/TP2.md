# Trabajo Práctico N°2 – Mini API de Tareas con FastAPI

## Objetivo
- Manejar **path params** y **query params** en rutas.
- Usar correctamente los métodos **GET**, **POST**, **PUT** y **DELETE**.
- Validar datos de entrada y devolver **respuestas claras con códigos de estado HTTP**.
- Construir respuestas en formato **JSON estructurado**.
- Implementar un CRUD básico en memoria aplicando buenas prácticas.

## Contexto

En el trabajo anterior, implementamos una agenda de contactos que solo permitía listar información con el método GET.
Ahora, avanzarás un paso más: crearás una Mini API de Tareas, donde podrás crear, leer, actualizar y eliminar tareas en memoria.

Este proyecto te permitirá practicar el manejo de parámetros, validaciones y el uso de múltiples métodos HTTP en FastAPI.

## 1. CRUD de Tareas
Implementa un sistema en memoria para manejar tareas, con las siguientes rutas:

- **GET /tareas** → devuelve todas las tareas.
- **POST /tareas** → agrega una nueva tarea.
- Validar que el campo descripcion no esté vacío.
- **PUT /tareas/{id}** → modifica una tarea existente según su id.
- **DELETE /tareas/{id}** → elimina una tarea existente.

Cada tarea debe tener al menos:

```json
{
    "id": int,
    "descripcion": str,
    "estado": str ("pendiente" | "en_progreso" | "completada")
}
```

## 2. Funcionalidades adicionales obligatorias

Para subir un poco el nivel respecto al TP anterior, tu API debe incluir además:

- **Búsqueda con query params**
    - `GET /tareas?estado=pending` → filtra tareas según el estado.   
    - `GET /tareas?texto=palabra` → busca tareas que contengan esa palabra en la descripción.

- **Validación de errores con códigos HTTP adecuados**
    - Intentar editar/eliminar una tarea que no existe → retornar `404`.
    - Intentar crear una tarea con descripción vacía → retornar `400`.
    - Todas las respuestas deben ser claras y devolver mensajes en JSON, por ejemplo:

    ```json
    { "error": "La tarea no existe" }
    ```

- **Contador de tareas por estado**
    - Ruta: `GET /tareas/resumen`
    - Ejemplo de respuesta:
        ```json
        {
            "pendiente": 2,
            "en_progreso": 1,
            "completada": 3
        }
        ```
- **Fecha de creación de la tarea**
    - Al crear una tarea, registrar automáticamente la fecha y hora.
- **Marcar todas las tareas como completadas**
    - Ruta: `PUT /tareas/completar_todas`

## 3. Control de estados válidos

- Solo se deben aceptar los valores `"pendiente"`, `"en_progreso"`, `"completada"`.

- Si se envía otro valor, retornar `400`.

---

## Fecha de entrega
**[IMPORTANTE]**

El trabajo debe presentarse hasta el 10 de OCTUBRE de 2025 a las 21:00hs.

---

## Testeo del práctico
1. **Instalar dependencias**:

    Instala las dependencias requeridas:

    ```bash
    pip install pytest requests httpx # Instala las librerias en el entorno
    ```

2. **Verificar la estructura del proyecto**:

    Asegúrate de que el archivo con los tests (por ejemplo, test_TP2.py) y el archivo main.py (que contiene la aplicación FastAPI) estén en el mismo directorio o en una estructura accesible.

3. **Ejecutar los tests**

    - **Abrir una terminal**: Navega al directorio donde están los archivos test_TP2.py y main.py.
    - **Ejecutar pytest**: Usa el comando

        ```bash
        pytest test_TP2.py -v
        ```

    - -v habilita el modo verboso para ver detalles de cada prueba.
    - Esto ejecutará todos los tests definidos en el archivo (test_01 a test_20).

4. **Opcional: Ejecutar un test específico**:

    Si quieres ejecutar un solo test, por ejemplo, test_07_crear_tarea_exitosamente, usa:

    ```bash
    pytest test_TP2.py::test_07_crear_tarea_exitosamente -v
    ```

5. **Verificar los resultados**

    
    **Salida esperada**: pytest mostrará un resumen de los tests ejecutados, indicando cuántos pasaron, fallaron o fueron omitidos.

    Ejemplo de salida exitosa
    ```bash
    ============================= test session starts =============================
    test_TP2.py::test_01_obtener_tareas_vacia PASSED
    test_TP2.py::test_02_obtener_todas_las_tareas PASSED
    ...
    test_TP2.py::test_20_completar_todas_sin_tareas PASSED
    ========================= 20 passed in 0.12s =========================
    ```

    - Si algún test falla, revisa el mensaje de error para identificar el problema (por ejemplo, un endpoint mal implementado en main.py o un problema con las aserciones).
