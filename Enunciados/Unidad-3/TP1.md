# TP3.1: Introducción a FastAPI - Servidor Básico

## Objetivo
Desarrollar un servidor básico con FastAPI que exponga endpoints simples para una Agenda de contactos, utilizando datos estáticos en memoria.

## Estructura de datos

La Agenda es una lista de contactos en memoria.
Los Contactos contienen: **nombre, apellido, edad, teléfono y email.**

## Funcionalidad
El sistema debe:

- Crear un servidor FastAPI básico.
- Exponer un endpoint GET raíz que devuelva un mensaje de bienvenida.
- Exponer un endpoint GET para listar contactos estáticos (hardcoded).
- Mínimo 10 contactos deben ser cargados y mostrados.
- Incluir manejo básico de errores (e.g., 404).
- Ejecutar el servidor con uvicorn.
- Los contactos se deben mostrar en formato JSON.

## Ejemplo de ejecución del sistema
=== AGENDA DE CONTACTOS API ===
- Ejecutar: `uvicorn main:app --reload`
- Visitar http://127.0.0.1:8000/
    - Respuesta: 
    ```json
    {"mensaje": "Bienvenido a la Agenda de Contactos API"}
    ```
- Visitar http://127.0.0.1:8000/contactos
    - Respuesta: 
    ```json 
    [
        {"nombre": "Juan", "apellido": "Pérez", "edad": 30, "teléfono": "3815551234", "email": "jperez@gmail.com"},
        {"nombre": "José", "apellido": "Gómez", "edad": 25, "teléfono": "3815551235", "email": "jgomez@gmail.com"}
    ] 
    ```

---
## Fecha de entrega
**[IMPORTANTE]**

El trabajo debe presentarse hasta el 3 de OCTUBRE de 2025 a las 21:00hs.


--- 
> Nota: Los alumnos que deseen pueden utilizar el siguiente requirements.txt

```txt
fastapi==0.104.1 
uvicorn[standard]==0.24.0
requests==2.31.0
pytest==7.4.3
```