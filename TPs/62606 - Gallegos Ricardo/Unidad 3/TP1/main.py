from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any
import uvicorn

# Crear la aplicación FastAPI
app = FastAPI()

# Estructura de datos: Lista de contactos estáticos en memoria
contactos_db: List[Dict[str, Any]] = [
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
    }
    # Podés seguir agregando hasta llegar a los 10 o más contactos
]

@app.get("/")
async def root():
    """
    Endpoint raíz que devuelve un mensaje de bienvenida
    """
    return {"mensaje": "Bienvenido a la Agenda de Contactos API"}

@app.get("/contactos")
async def obtener_contactos():
    """
    Endpoint para obtener todos los contactos de la agenda
    """
    return contactos_db

if __name__ == "__main__":
    print("== AGENDA DE CONTACTOS API ==")
    print("Iniciando servidor...")
    print("Visita:   http://127.0.0.1:8000/")
    print("Contactos: http://127.0.0.1:8000/contactos")

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )

