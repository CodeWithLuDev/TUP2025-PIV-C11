from fastapi import FastAPI, HTTPException

# Creamos la aplicación principal de FastAPI
app = FastAPI()

# Definimos la "agenda" como una lista de contactos en memoria
# Cada contacto es un diccionario con nombre, apellido, edad, teléfono y email
contactos = [
    {"nombre": "Juan", "apellido": "Pérez", "edad": 30, "telefono": "3815551234", "email": "jperez@gmail.com"},
    {"nombre": "José", "apellido": "Gómez", "edad": 25, "telefono": "3815551235", "email": "jgomez@gmail.com"},
    {"nombre": "María", "apellido": "López", "edad": 28, "telefono": "3815551236", "email": "mlopez@gmail.com"},
    {"nombre": "Ana", "apellido": "Martínez", "edad": 32, "telefono": "3815551237", "email": "amartinez@gmail.com"},
    {"nombre": "Luis", "apellido": "Fernández", "edad": 40, "telefono": "3815551238", "email": "lfernandez@gmail.com"},
    {"nombre": "Carla", "apellido": "Rodríguez", "edad": 22, "telefono": "3815551239", "email": "crodriguez@gmail.com"},
    {"nombre": "Pablo", "apellido": "Sánchez", "edad": 27, "telefono": "3815551240", "email": "psanchez@gmail.com"},
    {"nombre": "Sofía", "apellido": "Díaz", "edad": 35, "telefono": "3815551241", "email": "sdiaz@gmail.com"},
    {"nombre": "Martín", "apellido": "Torres", "edad": 29, "telefono": "3815551242", "email": "mtorres@gmail.com"},
    {"nombre": "Laura", "apellido": "Ruiz", "edad": 31, "telefono": "3815551243", "email": "lruiz@gmail.com"},
]

# Endpoint raíz: devuelve un mensaje de bienvenida
@app.get("/")
def leer_raiz():
    return {"mensaje": "Bienvenido a la Agenda de Contactos API"}

# Endpoint para listar todos los contactos
@app.get("/contactos")
def listar_contactos():
    return contactos

# Endpoint para buscar un contacto por índice (posición en la lista)
# Ejemplo: http://127.0.0.1:8000/contactos/3
@app.get("/contactos/{contacto_id}")
def obtener_contacto(contacto_id: int):
    # Verificamos que el índice esté dentro del rango de la lista
    if 0 <= contacto_id < len(contactos):
        return contactos[contacto_id]
    else:
        # Si no existe, devolvemos un error 404
        raise HTTPException(status_code=404, detail="Contacto no encontrado")