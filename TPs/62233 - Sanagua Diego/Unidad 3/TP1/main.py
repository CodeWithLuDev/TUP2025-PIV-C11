from fastapi import FastAPI, HTTPException 
from typing import List, Dict, Any
import uvicorn

# Crear la aplicación FastAPI
app = FastAPI()

# Estructura de datos: Lista de contactos estáticos en memoria
contactos_db: List[Dict[str, Any]] = [
    {"nombre": "Diego", "apellido": "Sanagua", "edad": 25, "teléfono": "3815551201", "email": "camila.torres@gmail.com"},
    {"nombre": "Lionel", "apellido": "Messi", "edad": 35, "teléfono": "3815551209", "email": "lionel.messi@gmail.com"},
    {"nombre": "Emiliano", "apellido": "Martínez", "edad": 30, "teléfono": "3815551201", "email": "emiliano.martinez@gmail.com"},
    {"nombre": "Nahuel", "apellido": "Molina", "edad": 24, "teléfono": "3815551202", "email": "nahuel.molina@gmail.com"},
    {"nombre": "Cristian", "apellido": "Romero", "edad": 24, "teléfono": "3815551203", "email": "cristian.romero@gmail.com"},
    {"nombre": "Nicolás", "apellido": "Otamendi", "edad": 34, "teléfono": "3815551204", "email": "nicolas.otamendi@gmail.com"},
    {"nombre": "Nicolás", "apellido": "Tagliafico", "edad": 30, "teléfono": "3815551205", "email": "nicolas.tagliafico@gmail.com"},
    {"nombre": "Rodrigo", "apellido": "De Paul", "edad": 28, "teléfono": "3815551206", "email": "rodrigo.depaul@gmail.com"},
    {"nombre": "Enzo", "apellido": "Fernández", "edad": 21, "teléfono": "3815551207", "email": "enzo.fernandez@gmail.com"},
    {"nombre": "Alexis", "apellido": "Mac Allister", "edad": 23, "teléfono": "3815551208", "email": "alexis.macallister@gmail.com"},
    {"nombre": "Julián", "apellido": "Álvarez", "edad": 22, "teléfono": "3815551210", "email": "julian.alvarez@gmail.com"},
    {"nombre": "Ángel", "apellido": "Di María", "edad": 34, "teléfono": "3815551211", "email": "angel.dimaria@gmail.com"}
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

