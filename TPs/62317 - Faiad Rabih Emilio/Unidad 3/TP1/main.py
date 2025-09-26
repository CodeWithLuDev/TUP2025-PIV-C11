import fastapi
from fastapi import FastAPI, HTTPException
from typing import List
from pydantic import BaseModel

app = FastAPI()

# Clase de contactos
class Contacto(BaseModel):
    nombre: str
    apellido: str
    edad: int
    teléfono: str
    email: str

# Lista de contactos
contactos: List[Contacto] = [
    Contacto(nombre="Juan", apellido="Pérez", edad=30, teléfono="3815551234", email="jperez@gmail.com"),
    Contacto(nombre="José", apellido="Gómez", edad=25, teléfono="3815551235", email="jgomez@gmail.com"),
    Contacto(nombre="Dolores", apellido="Delano", edad=281, teléfono="3815551236", email="mduele@gmail.com"),
    Contacto(nombre="Ana", apellido="Martinez", edad=69, teléfono="3815551237", email="amartinez@gmail.com"),
    Contacto(nombre="Carlitos", apellido="Bala", edad=100, teléfono="3815551238", email="cbala@gmail.com"),
    Contacto(nombre="Lucia", apellido="Fernandez", edad=21, teléfono="3815551239", email="lfernandez@gmail.com"),
    Contacto(nombre="Rigoberto", apellido="Sanchez", edad=42, teléfono="3815551240", email="rsanchez@gmail.com"),
    Contacto(nombre="Sofia", apellido="Garcia", edad=1, teléfono="3815551241", email="gugugaga@gmail.com"),
    Contacto(nombre="Raton", apellido="Perez", edad=-553, teléfono="3815551242", email="teefs@gmail.com"),
    Contacto(nombre="Laura", apellido="Torres", edad=25151, teléfono="3815551243", email="ltorres@gmail.com")
]

# Endpoints
@app.get("/")
async def bienvenida():
    return {"mensaje": "Welcome to the jungle, we got fun and games -- digo, Bienvenido a la Agenda de Contactos, o algo asi..."}
@app.get("/contactos", response_model=List[Contacto])
async def listar_contactos():
    return contactos

@app.get("/contactos/{nombre}", response_model=Contacto)
async def obtener_contacto(nombre: str):
    for contacto in contactos:
        if contacto.nombre.lower() == nombre.lower():
            return contacto
    raise HTTPException(status_code=404, detail="No existe dicho pibe")