"""
TP3.1: Introducción a FastAPI - Servidor Básico
Agenda de Contactos API

Este archivo implementa un servidor FastAPI que expone
endpoints simples para trabajar con una agenda de contactos
estática en memoria.
"""

from fastapi import FastAPI
from typing import List, Dict, Any
import uvicorn

# Crear la aplicación principal de FastAPI
# Aquí definimos la "app" que servirá como punto de entrada de la API
app = FastAPI(
    title="Agenda de Contactos API",
    description="API básica para listar contactos en memoria",
    version="1.0.0",
)

# Estructura de datos en memoria (simulación de una base de datos)
# Cada contacto es un diccionario con nombre, apellido, edad, teléfono y email
contactos_agenda: List[Dict[str, Any]] = [
    {
        "nombre": "Juan",
        "apellido": "Pérez",
        "edad": 30,
        "teléfono": "3815551242",
        "email": "jperez@gmail.com",
    },
    {
        "nombre": "José",
        "apellido": "Gómez",
        "edad": 25,
        "teléfono": "3815551235",
        "email": "jgomez@gmail.com",
    },
    {
        "nombre": "María",
        "apellido": "García",
        "edad": 28,
        "teléfono": "3815551236",
        "email": "mgarcia@gmail.com",
    },
    {
        "nombre": "Carlos",
        "apellido": "López",
        "edad": 35,
        "teléfono": "3815551237",
        "email": "clopez@gmail.com",
    },
    {
        "nombre": "Ana",
        "apellido": "Martínez",
        "edad": 22,
        "teléfono": "3815551238",
        "email": "amartinez@gmail.com",
    },
    {
        "nombre": "Luis",
        "apellido": "Rodríguez",
        "edad": 40,
        "teléfono": "3815551239",
        "email": "lrodriguez@gmail.com",
    },
    {
        "nombre": "Laura",
        "apellido": "Fernández",
        "edad": 26,
        "teléfono": "3815551240",
        "email": "lfernandez@gmail.com",
    },
    {
        "nombre": "Diego",
        "apellido": "Sánchez",
        "edad": 32,
        "teléfono": "3815551241",
        "email": "dsanchez@gmail.com",
    },
]


# Endpoint raíz (GET "/")
# Devuelve un mensaje de bienvenida
@app.get("/")
async def raiz():
    return {"mensaje": "Bienvenido a la Agenda de Contactos API"}


# Endpoint para listar todos los contactos (GET "/contactos")
# Devuelve la lista completa de contactos en formato JSON
@app.get("/contactos")
async def listar_contactos():
    return contactos_agenda


# Bloque principal para ejecutar el servidor con uvicorn
# Permite correr la app con: python main.py
if __name__ == "__main__":
    print("=== AGENDA DE CONTACTOS API ===")
    print("Servidor ejecutándose en http://127.0.0.1:8000/")
    print("Documentación automática en http://127.0.0.1:8000/docs")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
