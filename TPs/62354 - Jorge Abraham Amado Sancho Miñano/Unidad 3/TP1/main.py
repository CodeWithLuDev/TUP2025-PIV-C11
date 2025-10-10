from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI(title="Agenda de Contactos API")

# Datos estáticos en memoria
agenda_contactos = [
    {"nombre": "Juan", "apellido": "Pérez", "edad": 30, "teléfono": "3815551234", "email": "jperez@gmail.com"},
    {"nombre": "José", "apellido": "Gómez", "edad": 25, "teléfono": "3815551235", "email": "jgomez@gmail.com"},
    {"nombre": "Ana", "apellido": "López", "edad": 28, "teléfono": "3815551236", "email": "alopez@gmail.com"},
    {"nombre": "Luis", "apellido": "Martínez", "edad": 35, "teléfono": "3815551237", "email": "lmartinez@gmail.com"},
    {"nombre": "María", "apellido": "Rodríguez", "edad": 32, "teléfono": "3815551238", "email": "mrodriguez@gmail.com"},
    {"nombre": "Carlos", "apellido": "Sánchez", "edad": 40, "teléfono": "3815551239", "email": "csanchez@gmail.com"},
    {"nombre": "Lucía", "apellido": "Fernández", "edad": 27, "teléfono": "3815551240", "email": "lfernandez@gmail.com"},
    {"nombre": "Pedro", "apellido": "Ramírez", "edad": 29, "teléfono": "3815551241", "email": "pramirez@gmail.com"},
    {"nombre": "Sofía", "apellido": "Torres", "edad": 31, "teléfono": "3815551242", "email": "storres@gmail.com"},
    {"nombre": "Diego", "apellido": "Gutiérrez", "edad": 33, "teléfono": "3815551243", "email": "dgutierrez@gmail.com"}
]

# Endpoint raíz
@app.get("/")
def bienvenida():
    return {"mensaje": "Bienvenido a la Agenda de Contactos API"}

# Endpoint para listar contactos
@app.get("/contactos")
def listar_contactos():
    return JSONResponse(content=agenda_contactos)

# Manejo básico de errores
@app.get("/contactos/{contacto_id}")
def obtener_contacto(contacto_id: int):
    if 0 <= contacto_id < len(agenda_contactos):
        return agenda_contactos[contacto_id]
    raise HTTPException(status_code=404, detail="Contacto no encontrado")