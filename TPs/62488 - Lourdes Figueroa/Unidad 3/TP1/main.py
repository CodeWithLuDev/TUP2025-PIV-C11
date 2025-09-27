from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

class Contacto(BaseModel):
    nombre: str
    apellido: str
    edad: int
    telefono: str
    email: str
    
app = FastAPI(title="Agenda de contactos API")

contactos = [
    Contacto(nombre="Antonela", apellido="Bernuncio", edad=24, telefono="3865433621", email="antobernuncio@gmail.com"),
    Contacto(nombre="Canela", apellido="Bulacio", edad=24, telefono="3865693258", email="cbulacion@gmail.com"),
    Contacto(nombre="Daniela", apellido="Orlando", edad=29, telefono="3865445895", email="danielaor102@gmail.com"),
    Contacto(nombre="Delfina", apellido="Vallina", edad=23, telefono="3865693247", email="delfivalli@gmail.com"),
    Contacto(nombre="Guillermina", apellido="Dande", edad=21, telefono="3865213698", email="guillermina098@gmail.com"),
    Contacto(nombre="Josefina", apellido="Orlando", edad=26, telefono="3865250089", email="orlandojose@gmail.com"),
    Contacto(nombre="Julieta", apellido="Herrera", edad=34, telefono="3865470258", email="julihe@gmail.com"),
    Contacto(nombre="Karen", apellido="Reyes", edad=24, telefono="3865479633", email="karen_reyes@gmail.com"),
    Contacto(nombre="Florencia", apellido="Jimenez", edad=19, telefono="3865695541", email="florjime@gmail.com"),
    Contacto(nombre="Nora", apellido="Figueroa", edad=38, telefono="3865693715", email="norafigueroa@gmail.com"),
]

@app.get("/")
async def raiz():
    return{"mensaje":"Bienvenido a la Agenda de Contactos"}

@app.get("/contactos", response_model=List[Contacto])
async def listar_contactos():
    if not contactos:
        raise HTTPException(status_code=404, detail="No se encontraron contactos")
    return contactos
