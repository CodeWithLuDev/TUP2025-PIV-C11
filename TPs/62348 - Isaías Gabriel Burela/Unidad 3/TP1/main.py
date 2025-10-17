# main.py
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Agenda de Contactos API", version="1.0")

# Datos estáticos en memoria: lista de diccionarios (mínimo 10 contactos)
CONTACTOS = [
    {"id": 1, "nombre": "Juan",    "apellido": "Pérez",      "edad": 30, "teléfono": "3815551234", "email": "jperez@gmail.com"},
    {"id": 2, "nombre": "María",   "apellido": "García",     "edad": 28, "teléfono": "3815551235", "email": "mgarcia@gmail.com"},
    {"id": 3, "nombre": "Carlos",  "apellido": "Rodríguez",  "edad": 35, "teléfono": "3815551236", "email": "crodri@gmail.com"},
    {"id": 4, "nombre": "Lucía",   "apellido": "López",      "edad": 22, "teléfono": "3815551237", "email": "llopez@gmail.com"},
    {"id": 5, "nombre": "Mariano", "apellido": "Sosa",       "edad": 40, "teléfono": "3815551238", "email": "msosa@gmail.com"},
    {"id": 6, "nombre": "Sofía",   "apellido": "Fernández",  "edad": 27, "teléfono": "3815551239", "email": "sofiaf@gmail.com"},
    {"id": 7, "nombre": "Diego",   "apellido": "Martínez",   "edad": 33, "teléfono": "3815551240", "email": "dmartinez@gmail.com"},
    {"id": 8, "nombre": "Valentina","apellido":"Ruiz",       "edad": 26, "teléfono": "3815551241", "email": "valruiz@gmail.com"},
    {"id": 9, "nombre": "Pablo",   "apellido": "Alvarez",    "edad": 45, "teléfono": "3815551242", "email": "palvarez@gmail.com"},
    {"id":10, "nombre": "Camila",  "apellido": "Torres",     "edad": 31, "teléfono": "3815551243", "email": "ctorres@gmail.com"}
]

@app.get("/")
async def raiz():
    """
    Endpoint raíz.
    GET http://127.0.0.1:8000/
    """
    return {"mensaje": "Bienvenido a la Agenda de Contactos appi de isaias"}

@app.get("/contactos")
async def listar_contactos():
    """
    Devuelve la lista completa de contactos (JSON).
    GET http://127.0.0.1:8000/contactos
    """
    return CONTACTOS

@app.get("/contactos/{contact_id}")
async def obtener_contacto(contact_id: int):
    """
    Devuelve un contacto por su id.
    Si no existe, lanza un HTTPException con código 404.
    Ejemplo: GET http://127.0.0.1:8000/contactos/3
    """
    for contacto in CONTACTOS:
        if contacto["id"] == contact_id:
            return contacto
    # Manejo básico de error: contacto no encontrado -> 404
    raise HTTPException(status_code=404, detail="Contacto no encontrado")
