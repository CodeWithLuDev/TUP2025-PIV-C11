from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import json



contactos=[
  {"nombre": "Juan", "apellido": "Pérez", "edad": 30, "telefono": "3815551234", "email": "juan.perez@gmail.com"},
  {"nombre": "María", "apellido": "García", "edad": 27, "telefono": "3815551235", "email": "maria.garcia@gmail.com"},
  {"nombre": "Lucía", "apellido": "Fernández", "edad": 35, "telefono": "3815551236", "email": "lucia.fernandez@gmail.com"},
  {"nombre": "Carlos", "apellido": "Sánchez", "edad": 22, "telefono": "3815551237", "email": "carlos.sanchez@gmail.com"},
  {"nombre": "Ana", "apellido": "López", "edad": 40, "telefono": "3815551238", "email": "ana.lopez@gmail.com"},
  {"nombre": "Sofía", "apellido": "Martínez", "edad": 29, "telefono": "3815551239", "email": "sofia.martinez@gmail.com"},
  {"nombre": "Pedro", "apellido": "Gómez", "edad": 33, "telefono": "3815551240", "email": "pedro.gomez@gmail.com"},
  {"nombre": "Valentina", "apellido": "Romero", "edad": 26, "telefono": "3815551241", "email": "valentina.romero@gmail.com"},
  {"nombre": "Martín", "apellido": "Díaz", "edad": 31, "telefono": "3815551242", "email": "martin.diaz@gmail.com"},
  {"nombre": "Florencia", "apellido": "Vega", "edad": 24, "telefono": "3815551243", "email": "florencia.vega@gmail.com"}
]

app = FastAPI()
@app.get("/")
def raiz():
    """
    Endpoint raíz: mensaje de bienvenida.
    """
    return {"mensaje": "Bienvenido a la Agenda de Contactos API"}

@app.get("/contactos")
def listar_contactos():
    """
    Devuelve la lista completa de contactos (formato JSON).
    """
    return contactos

@app.get("/contactos/{contact_id}")
def obtener_contacto(contact_id: int):
    """
    Devuelve un único contacto por su índice (0-based).
    Si no existe, devuelve 404.
    """
    if 0 <= contact_id < len(contactos):
        return contactos[contact_id]
    raise HTTPException(status_code=404, detail="Contacto no encontrado")
