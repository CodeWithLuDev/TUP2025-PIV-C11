"""
TP3.1: Introducción a FastAPI - Servidor Básico
Agenda de Contactos API

Este archivo contiene la implementación del servidor FastAPI
que expone endpoints para una agenda de contactos harcodeados.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import List, Dict, Any

# Crear la aplicación FastAPI
app = FastAPI(
    title="Agenda de Contactos API",
    description="API básica para gestionar contactos",
    version="1.0.0"
)

# Lista de contactos estáticos (hardcoded) en memoria
# Mínimo 10 contactos como requiere el TP
contactos_agenda: List[Dict[str, Any]] = [
    {
        "nombre": "Juan",
        "apellido": "Pérez", 
        "edad": 30,
        "teléfono": "3815551234",
        "email": "jperez@gmail.com"
    },
    {
        "nombre": "José",
        "apellido": "Gómez",
        "edad": 25,
        "teléfono": "3815551235", 
        "email": "jgomez@gmail.com"
    },
    {
        "nombre": "María",
        "apellido": "García",
        "edad": 28,
        "teléfono": "3815551236",
        "email": "mgarcia@gmail.com"
    },
    {
        "nombre": "Carlos",
        "apellido": "López",
        "edad": 35,
        "teléfono": "3815551237",
        "email": "clopez@gmail.com"
    },
    {
        "nombre": "Ana",
        "apellido": "Martínez",
        "edad": 22,
        "teléfono": "3815551238",
        "email": "amartinez@gmail.com"
    },
    {
        "nombre": "Luis",
        "apellido": "Rodríguez",
        "edad": 40,
        "teléfono": "3815551239",
        "email": "lrodriguez@gmail.com"
    },
    {
        "nombre": "Laura",
        "apellido": "Fernández",
        "edad": 26,
        "teléfono": "3815551240",
        "email": "lfernandez@gmail.com"
    },
    {
        "nombre": "Diego",
        "apellido": "Sánchez",
        "edad": 32,
        "teléfono": "3815551241",
        "email": "dsanchez@gmail.com"
    },
    {
        "nombre": "Sofía",
        "apellido": "Herrera",
        "edad": 24,
        "teléfono": "3815551242",
        "email": "sherrera@gmail.com"
    },
    {
        "nombre": "Roberto",
        "apellido": "Jiménez",
        "edad": 38,
        "teléfono": "3815551243",
        "email": "rjimenez@gmail.com"
    },
    {
        "nombre": "Valentina",
        "apellido": "Torres",
        "edad": 29,
        "teléfono": "3815551244",
        "email": "vtorres@gmail.com"
    },
    {
        "nombre": "Andrés",
        "apellido": "Vargas",
        "edad": 33,
        "teléfono": "3815551245",
        "email": "avargas@gmail.com"
    }
]


@app.get("/")
async def endpoint_raiz():
    """
    Endpoint raíz que devuelve un mensaje de bienvenida.
    
    Returns:
        Dict: Mensaje de bienvenida en formato JSON
    """
    return {"mensaje": "Bienvenido a la Agenda de Contactos API"}


@app.get("/contactos")
async def obtener_contactos():
    """
    Endpoint para obtener todos los contactos de la agenda.
    
    Returns:
        List[Dict]: Lista de contactos en formato JSON
    """
    return contactos_agenda


# Manejo de errores 404 para rutas no encontradas
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """
    Manejo personalizado de errores 404.
    
    Args:
        request: La petición HTTP
        exc: La excepción 404
        
    Returns:
        JSONResponse: Mensaje de error en formato JSON
    """
    return JSONResponse(
        status_code=404,
        content={"error": "Ruta no encontrada", "mensaje": "La URL solicitada no existe"}
    )


# Función para ejecutar el servidor (opcional)
if __name__ == "__main__":
    import uvicorn
    print("=== AGENDA DE CONTACTOS API ===")
    print("Ejecutando servidor...")
    print("Visita: http://127.0.0.1:8000/")
    print("Documentación: http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="127.0.0.1", port=8000)
