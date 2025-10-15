from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any
import uvicorn

# Crear la aplicación FastAPI
app = FastAPI()

# Base de datos simulada en memoria (lista de diccionarios)
contactos_db: List[Dict[str, Any]] = [
    {"nombre": "Camila",    "apellido": "Torres",    "edad": 27, "teléfono": "3815551201", "email": "camila.torres@gmail.com"},
    {"nombre": "Mateo",     "apellido": "Luna",      "edad": 31, "teléfono": "3815551202", "email": "mateo.luna@gmail.com"},
    {"nombre": "Valentina", "apellido": "Suárez",    "edad": 24, "teléfono": "3815551203", "email": "valentina.suarez@gmail.com"},
    {"nombre": "Ignacio",   "apellido": "Ramírez",   "edad": 35, "teléfono": "3815551204", "email": "ignacio.ramirez@gmail.com"},
    {"nombre": "Florencia", "apellido": "Molina",    "edad": 29, "teléfono": "3815551205", "email": "florencia.molina@gmail.com"},
    {"nombre": "Bruno",     "apellido": "Acosta",    "edad": 33, "teléfono": "3815551206", "email": "bruno.acosta@gmail.com"},
    {"nombre": "Paula",     "apellido": "Benítez",   "edad": 26, "teléfono": "3815551207", "email": "paula.benitez@gmail.com"},
    {"nombre": "Leandro",   "apellido": "Paz",       "edad": 38, "teléfono": "3815551208", "email": "leandro.paz@gmail.com"},
    {"nombre": "Martina",   "apellido": "Herrera",   "edad": 23, "teléfono": "3815551209", "email": "martina.herrera@gmail.com"},
    {"nombre": "Santiago",  "apellido": "Figueroa",  "edad": 30, "teléfono": "3815551210", "email": "santiago.figueroa@gmail.com"}
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

@app.get("/contacto/{indice}")
async def obtener_contacto(indice: int):
    """
    Endpoint para obtener un contacto específico por índice
    """
    if 0 <= indice < len(contactos_db):
        return contactos_db[indice]
    raise HTTPException(status_code=404, detail="Contacto no encontrado")

if __name__ == "__main__":
    print("=== AGENDA DE CONTACTOS API ===")
    print("Iniciando servidor...")
    print("Visita la API en:           http://127.0.0.1:8000/")
    print("Ver todos los contactos en: http://127.0.0.1:8000/contactos")
    print("Ver contacto individual en: http://127.0.0.1:8000/contacto/0")

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
