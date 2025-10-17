from fastapi import FastAPI, HTTPException

app = FastAPI()

# Datos estáticos en memoria
contactos = [
    {"nombre": "Juan", "apellido": "Pérez", "edad": 30, "teléfono": "3815551234", "email": "jperez@gmail.com"},
    {"nombre": "José", "apellido": "Gómez", "edad": 25, "teléfono": "3815551235", "email": "jgomez@gmail.com"},
    {"nombre": "Ana", "apellido": "Martínez", "edad": 28, "teléfono": "3815551236", "email": "amartinez@gmail.com"},
    {"nombre": "Luis", "apellido": "Rodríguez", "edad": 35, "teléfono": "3815551237", "email": "lrodriguez@gmail.com"},
    {"nombre": "María", "apellido": "Fernández", "edad": 32, "teléfono": "3815551238", "email": "mfernandez@gmail.com"},
    {"nombre": "Carlos", "apellido": "López", "edad": 40, "teléfono": "3815551239", "email": "clopez@gmail.com"},
    {"nombre": "Lucía", "apellido": "García", "edad": 27, "teléfono": "3815551240", "email": "lgarcia@gmail.com"},
    {"nombre": "Pedro", "apellido": "Sánchez", "edad": 29, "teléfono": "3815551241", "email": "psanchez@gmail.com"},
    {"nombre": "Sofía", "apellido": "Ramírez", "edad": 31, "teléfono": "3815551242", "email": "sramirez@gmail.com"},
    {"nombre": "Diego", "apellido": "Torres", "edad": 33, "teléfono": "3815551243", "email": "dtorres@gmail.com"}
]

# Endpoint raíz
@app.get("/")
def leer_raiz():
    return {"mensaje": "Bienvenido a la Agenda de Contactos API"}

# Endpoint para listar contactos
@app.get("/contactos")
def listar_contactos():
    return contactos

# Manejo básico de error 404
@app.get("/contactos/{contacto_id}")
def obtener_contacto(contacto_id: int):
    if contacto_id < 0 or contacto_id >= len(contactos):
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    return contactos[contacto_id]