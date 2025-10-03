from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"mensaje": "Bienvenido a la Agenda de Contactos API"}

from fastapi import HTTPException  

AGENDA = [
    {"nombre": "Juan",  "apellido": "Pérez",     "edad": 30, "telefono": "3815551234", "email": "juan.perez@example.com"},
    {"nombre": "José",  "apellido": "Gómez",     "edad": 25, "telefono": "3815551235", "email": "jose.gomez@example.com"},
    {"nombre": "María", "apellido": "López",     "edad": 28, "telefono": "3815551236", "email": "maria.lopez@example.com"},
    {"nombre": "Ana",   "apellido": "Martínez",  "edad": 22, "telefono": "3815551237", "email": "ana.martinez@example.com"},
    {"nombre": "Luis",  "apellido": "Rodríguez", "edad": 35, "telefono": "3815551238", "email": "luis.rodriguez@example.com"},
    {"nombre": "Sofía", "apellido": "Medina",    "edad": 27, "telefono": "3815551239", "email": "sofia.medina@example.com"},
    {"nombre": "Pedro", "apellido": "Rojas",     "edad": 32, "telefono": "3815551240", "email": "pedro.rojas@example.com"},
    {"nombre": "Lucía", "apellido": "Ferreyra",  "edad": 24, "telefono": "3815551241", "email": "lucia.ferreyra@example.com"},
    {"nombre": "Diego", "apellido": "Sosa",      "edad": 29, "telefono": "3815551242", "email": "diego.sosa@example.com"},
    {"nombre": "Carla", "apellido": "Álvarez",   "edad": 26, "telefono": "3815551243", "email": "carla.alvarez@example.com"},
]

@app.get("/contactos")
def listar_contactos():
    return AGENDA

@app.get("/contactos/{idx}")
def obtener_contacto(idx: int):
    if idx < 0 or idx >= len(AGENDA):
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    return AGENDA[idx]
