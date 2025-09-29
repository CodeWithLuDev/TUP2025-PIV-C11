from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from typing import List

# Modelo Pydantic
class Contacto(BaseModel):
    id: int
    nombre: str
    apellido: str
    edad: int
    telefono: str
    email: str

# Crear la aplicación
app = FastAPI(title="Agenda de Contactos", version="1.0")

# Lista de contactos 
contactos: List[Contacto] = [
    Contacto(id=1, nombre="Jose", apellido="Pérez", edad=30, telefono="123456789", email="jose.perez@mail.com"),
    Contacto(id=2, nombre="María", apellido="Gómez", edad=25, telefono="987654321", email="maria.gomez@mail.com"),
    Contacto(id=3, nombre="Gonzalo", apellido="Ramírez", edad=40, telefono="456123789", email="gonzalo.ramirez@mail.com"),
    Contacto(id=4, nombre="Lucía", apellido="Martínez", edad=28, telefono="741852963", email="lucia.martinez@mail.com"),
    Contacto(id=5, nombre="Ana", apellido="Fernández", edad=35, telefono="369258147", email="ana.fernandez@mail.com"),
    Contacto(id=6, nombre="Pedro", apellido="Sánchez", edad=32, telefono="852963741", email="pedro.sanchez@mail.com"),
    Contacto(id=7, nombre="Laura", apellido="Díaz", edad=27, telefono="159753486", email="laura.diaz@mail.com"),
    Contacto(id=8, nombre="Franco", apellido="Suárez", edad=45, telefono="753951456", email="franco.suarez@mail.com"),
    Contacto(id=9, nombre="Valeria", apellido="Torres", edad=22, telefono="951357258", email="valeria.torres@mail.com"),
    Contacto(id=10, nombre="Diego", apellido="López", edad=38, telefono="456987123", email="diego.lopez@mail.com"),
]

# Endpoint raíz
@app.get("/")
def read_root():
    return {"mensaje": "Bienvenido a la Agenda de Contactos"}

# Endpoint para listar contactos
@app.get("/contactos", response_model=List[Contacto])
def listar_contactos():
    return contactos

# Endpoint para obtener un contacto por ID
@app.get("/contactos/{contacto_id}", response_model=Contacto)
def obtener_contacto(contacto_id: int):
    contacto = next((c for c in contactos if c.id == contacto_id), None)
    if contacto:
        return contacto
    raise HTTPException(status_code=404, detail="Contacto no encontrado")
