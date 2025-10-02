from fastapi import FastAPI, HTTPException
from typing import List
from pydantic import BaseModel


app = FastAPI()

class Contacto(BaseModel):
    nombre: str
    apellido: str
    edad: int
    telefono: str
    email: str

# 🧑‍🤝‍🧑 Lista de contactos en memoria
agenda: List[Contacto] = [
    Contacto(nombre="Luis", apellido="Vera", edad=30, telefono="3811234567", email="luis.vera@example.com"),
    Contacto(nombre="Micaela", apellido="Urquiza", edad=25, telefono="3812345678", email="mica.urquiza@example.com"),
    Contacto(nombre="Gonzalo", apellido="Chavez", edad=28, telefono="3813456789", email="gonzalo.chavez@example.com"),
    Contacto(nombre="Estela", apellido="Reyes", edad=35, telefono="3814567890", email="estela.reyes@example.com"),
    Contacto(nombre="Mariano", apellido="Moreno", edad=40, telefono="3815678901", email="mariano.moreno@example.com"),
    Contacto(nombre="Benjamin", apellido="Aguero", edad=22, telefono="3816789012", email="benjamin.aguero@example.com"),
    Contacto(nombre="Lautaro", apellido="Michael", edad=27, telefono="3817890123", email="lautaro.michael@example.com"),
    Contacto(nombre="Camila", apellido="Sosa", edad=29, telefono="3818901234", email="camila.sosa@example.com"),
    Contacto(nombre="Joaquin", apellido="Paz", edad=33, telefono="3819012345", email="joaquin.paz@example.com"),
    Contacto(nombre="Valentina", apellido="Lopez", edad=31, telefono="3810123456", email="valentina.lopez@example.com"),
]

# 🚪 Endpoint raíz
@app.get("/")
def bienvenida():
    return {"mensaje": "Bienvenido a la Agenda de Contactos con FastAPI"}

# 📋 Endpoint para listar contactos
@app.get("/contactos", response_model=List[Contacto])
def listar_contactos():
    return agenda

# ❌ Manejo básico de error 404 para rutas inexistentes
@app.get("/{ruta_invalida}")
def ruta_no_encontrada(ruta_invalida: str):
    raise HTTPException(status_code=404, detail="Ruta no encontrada")