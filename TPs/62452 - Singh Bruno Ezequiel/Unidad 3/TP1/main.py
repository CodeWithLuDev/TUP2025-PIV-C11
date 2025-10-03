from fastapi import FastAPI
from fastapi import HTTPException


# Creamos la aplicación FastAPI
app = FastAPI()

# Endpoint raíz (/)
@app.get("/")
def read_root():
    return {"mensaje": "Bienvenido a la Agenda de Contactos API"}

# Lista de contactos en memoria (10 contactos como mínimo)
contactos = [
    {"nombre": "Juan", "apellido": "Pérez", "edad": 30, "teléfono": "3815551234", "email": "jperez@gmail.com"},
    {"nombre": "Ana", "apellido": "García", "edad": 28, "teléfono": "3815555678", "email": "agarcia@gmail.com"},
    {"nombre": "Luis", "apellido": "Martínez", "edad": 35, "teléfono": "3815559876", "email": "lmartinez@gmail.com"},
    {"nombre": "María", "apellido": "López", "edad": 22, "teléfono": "3815554321", "email": "mlopez@gmail.com"},
    {"nombre": "Carlos", "apellido": "Fernández", "edad": 40, "teléfono": "3815552468", "email": "cfernandez@gmail.com"},
    {"nombre": "Lucía", "apellido": "Díaz", "edad": 27, "teléfono": "3815551357", "email": "ldiaz@gmail.com"},
    {"nombre": "Pedro", "apellido": "Suárez", "edad": 33, "teléfono": "3815558642", "email": "psuarez@gmail.com"},
    {"nombre": "Sofía", "apellido": "Romero", "edad": 29, "teléfono": "3815559753", "email": "sromero@gmail.com"},
    {"nombre": "Miguel", "apellido": "Castro", "edad": 31, "teléfono": "3815556547", "email": "mcastro@gmail.com"},
    {"nombre": "Valentina", "apellido": "Torres", "edad": 26, "teléfono": "3815553219", "email": "vtorres@gmail.com"}
]

# Endpoint /contactos
@app.get("/contactos")
def listar_contactos():
    return contactos

# Endpoint para obtener un contacto por ID (índice de la lista)
@app.get("/contactos/{contacto_id}")
def obtener_contacto(contacto_id: int):
    # Si el ID es válido (existe en la lista)
    if 0 <= contacto_id < len(contactos):
        return contactos[contacto_id]
    # Si no existe, lanzamos un error 404
    else:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
