from fastapi import FastAPI, HTTPException

app = FastAPI(title="Agenda de Contactos API de Lautaro")

# Lista estática de contactos
contactos = [
    {"nombre": "Juan", "apellido": "Pérez", "edad": 30, "teléfono": "3815551234", "email": "jperez@gmail.com"},
    {"nombre": "José", "apellido": "Gómez", "edad": 25, "teléfono": "3815551235", "email": "jgomez@gmail.com"},
    {"nombre": "Ana", "apellido": "Martínez", "edad": 28, "teléfono": "3815551236", "email": "amartinez@gmail.com"},
    {"nombre": "Laura", "apellido": "Ramírez", "edad": 22, "teléfono": "3815551237", "email": "lramirez@gmail.com"},
    {"nombre": "Carlos", "apellido": "Sánchez", "edad": 35, "teléfono": "3815551238", "email": "csanchez@gmail.com"},
    {"nombre": "María", "apellido": "Fernández", "edad": 27, "teléfono": "3815551239", "email": "mfernandez@gmail.com"},
    {"nombre": "Sofía", "apellido": "Torres", "edad": 31, "teléfono": "3815551240", "email": "storres@gmail.com"},
    {"nombre": "Pedro", "apellido": "Díaz", "edad": 29, "teléfono": "3815551241", "email": "pdiaz@gmail.com"},
    {"nombre": "Lucía", "apellido": "Molina", "edad": 24, "teléfono": "3815551242", "email": "lmolina@gmail.com"},
    {"nombre": "Andrés", "apellido": "Castro", "edad": 33, "teléfono": "3815551243", "email": "acastro@gmail.com"},
]

# Endpoint raíz
@app.get("/")
def read_root():
    return {"mensaje": "Bienvenido a la Agenda de Contactos API"}

# Endpoint para listar contactos
@app.get("/contactos")
def listar_contactos():
    return contactos

# Endpoint para obtener un contacto por índice
@app.get("/contactos/{contacto_id}")
def obtener_contacto(contacto_id: int):
    if 0 <= contacto_id < len(contactos):
        return contactos[contacto_id]
    raise HTTPException(status_code=404, detail="Contacto no encontrado")
