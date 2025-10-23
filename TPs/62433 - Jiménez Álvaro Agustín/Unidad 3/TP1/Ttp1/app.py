from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI(tittle="Agenda de Contactos")

class Contacto(BaseModel):
    id: int
    nombre: str
    apellido: str
    edad: int
    telefono: str
    email: str
contactos_db = [
    Contacto(id=1, nombre="Alvaro", apellido="Jimenez", edad=22, telefono="123456789", email="agusjimenez326@gmail.com"),
    Contacto(id=2, nombre="Gonzalo", apellido="Moreno", edad=28, telefono="123456798", email="gonzalomor@gmail.com"),
    Contacto(id=3, nombre="Exequiel", apellido="Costilla", edad=25, telefono="123456987", email="constillaexe@gmail.com"),
    Contacto(id=4, nombre="Jose", apellido="Acuña", edad=26, telefono="123459876", email="jose.acuna@gmail.com"),
    Contacto(id=5, nombre="Juan", apellido="Perez", edad=24, telefono="123498765", email="juan.perez@gmail.com"),
    Contacto(id=6, nombre="Maria", apellido="Gonzalez", edad=27, telefono="123487654", email="maria.gonzalez@gmail.com"),
    Contacto(id=7, nombre="Ana", apellido="Lopez", edad=23, telefono="123476543", email="ana.lopez@gmail.com"),
    Contacto(id=8, nombre="Luis", apellido="Martinez", edad=29, telefono="123465432", email="luis.martinez@gmail.com"),
    Contacto(id=9, nombre="Sofia", apellido="Rodriguez", edad=21, telefono="123454321", email="sofia.rodriguez@gmail.com"),
    Contacto(id=10, nombre="Carlos", apellido="Hernandez", edad=30, telefono="123443210", email="carlos.hernandez@gmail.com")
]

@app.get("/")
def read_root():
    return {"message": "¡Bienvenido a la Agenda de Contactos!"}

@app.get("/contactos", response_model=List[Contacto])
def listar_contactos():
    return contactos_db

@app.get("/contactos/{contacto_id}", response_model=Contacto)
def obtener_contacto(contacto_id: int):
    contacto = next((c for c in contactos_db if c.id == contacto_id), None)
    if contacto is None:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    return contacto

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Proyecto por Jimenez Alvaro Agustin - 62433