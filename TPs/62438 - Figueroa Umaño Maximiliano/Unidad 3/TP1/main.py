from fastapi import FastAPI, HTTPException

app = FastAPI()

# Lista de contactos (mínimo 10, hardcoded)
contactos = [
    {"nombre": "Juan", "apellido": "Pérez", "edad": 30, "telefono": "3815551234", "email": "jperez@gmail.com"},
    {"nombre": "José", "apellido": "Gómez", "edad": 25, "telefono": "3815551235", "email": "jgomez@gmail.com"},
    {"nombre": "María", "apellido": "García", "edad": 28, "telefono": "3815551236", "email": "mgarcia@gmail.com"},
    {"nombre": "Carlos", "apellido": "López", "edad": 35, "telefono": "3815551237", "email": "clopez@gmail.com"},
    {"nombre": "Ana", "apellido": "Martínez", "edad": 22, "telefono": "3815551238", "email": "amartinez@gmail.com"},
    {"nombre": "Luis", "apellido": "Rodríguez", "edad": 40, "telefono": "3815551239", "email": "lrodriguez@gmail.com"},
    {"nombre": "Laura", "apellido": "Fernández", "edad": 26, "telefono": "3815551240", "email": "lfernandez@gmail.com"},
    {"nombre": "Diego", "apellido": "Sánchez", "edad": 32, "telefono": "3815551241", "email": "dsanchez@gmail.com"},
    {"nombre": "Sofía", "apellido": "Herrera", "edad": 24, "telefono": "3815551242", "email": "sherrera@gmail.com"},
    {"nombre": "Roberto", "apellido": "Jiménez", "edad": 38, "telefono": "3815551243", "email": "rjimenez@gmail.com"},
]

# GET / → mensaje de bienvenida
@app.get("/")
def raiz():
    return {"mensaje": "Bienvenido a la Agenda de Contactos API"}

# GET /contactos → lista completa
@app.get("/contactos")
def listar_contactos():
    return contactos

# GET /contactos/{email} → buscar por email
@app.get("/contactos/{email}")
def obtener_contacto(email: str):
    for c in contactos:
        if c["email"].lower() == email.lower():
            return c
    raise HTTPException(status_code=404, detail="Contacto no encontrado")
