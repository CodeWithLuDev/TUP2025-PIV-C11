from fastapi import FastAPI, HTTPException

app = FastAPI(title="Agenda de Contactos – TP1")

AGENDA = [
    {"nombre": "Juan",  "apellido": "Pérez",     "edad": 30, "telefono": "3815551234", "email": "juan.perez@example.com"},
    {"nombre": "José",  "apellido": "Gómez",     "edad": 25, "telefono": "3815551235", "email": "jose.gomez@example.com"},
    {"nombre": "María", "apellido": "López",     "edad": 28, "telefono": "3815551236", "email": "maria.lopez@example.com"},
    {"nombre": "Ana",   "apellido": "Martínez",  "edad": 22, "telefono": "3815551237", "email": "ana.martinez@example.com"},
    {"nombre": "Luis",  "apellido": "Rodríguez", "edad": 35, "telefono": "3815551238", "email": "luis.rodriguez@example.com"},
    {"nombre": "Carlos","apellido": "Sosa",      "edad": 41, "telefono": "3815551239", "email": "carlos.sosa@example.com"},
    {"nombre": "Lucía", "apellido": "Ramos",     "edad": 19, "telefono": "3815551240", "email": "lucia.ramos@example.com"},
    {"nombre": "Sofía", "apellido": "Ruiz",      "edad": 33, "telefono": "3815551241", "email": "sofia.ruiz@example.com"},
    {"nombre": "Pablo", "apellido": "Cruz",      "edad": 27, "telefono": "3815551242", "email": "pablo.cruz@example.com"},
    {"nombre": "Marta", "apellido": "Vega",      "edad": 29, "telefono": "3815551243", "email": "marta.vega@example.com"},
]

@app.get("/")
def root():
    return {"mensaje": "Bienvenido a la Agenda de Contactos API"}

@app.get("/contactos")
def listar_contactos():
    return AGENDA

@app.get("/contactos/{idx}")
def obtener_contacto(idx: int):
    if 0 <= idx < len(AGENDA):
        return AGENDA[idx]
    raise HTTPException(status_code=404, detail="Contacto no encontrado")
