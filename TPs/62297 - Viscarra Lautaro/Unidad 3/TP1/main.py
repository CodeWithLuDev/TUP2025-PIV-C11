from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.get("/")
def read_root():
    return {"mensaje" : "Bienvenido a la lista de contactos"}

contactos = [
    {"nombre": "Juan", "apellido": "Pérez", "edad": 30, "telefono": "3815551234", "email": "jperez@gmail.com"},
    {"nombre": "Jose", "apellido": "Gómez", "edad": 25, "telefono": "3815551235", "email": "jgomez@gmail.com"},
    {"nombre": "Maria", "apellido": "López", "edad": 28, "telefono": "3815551236", "email": "mlopez@gmail.com"},
    {"nombre": "Ana", "apellido": "Martínez", "edad": 35, "telefono": "3815551237", "email": "amartinez@gmail.com"},
    {"nombre": "Luis", "apellido": "Rodríguez", "edad": 40, "telefono": "3815551238", "email": "lrodriguez@gmail.com"},
    {"nombre": "Carla", "apellido": "Fernández", "edad": 22, "telefono": "3815551239", "email": "cfernandez@gmail.com"},
    {"nombre": "Pedro", "apellido": "Díaz", "edad": 33, "telefono": "3815551240", "email": "pdiaz@gmail.com"},
    {"nombre": "Lucia", "apellido": "Ramírez", "edad": 29, "telefono": "3815551241", "email": "lramirez@gmail.com"},
    {"nombre": "Miguel", "apellido": "Torres", "edad": 31, "telefono": "3815551242", "email": "mtorres@gmail.com"},
    {"nombre": "Sofia", "apellido": "García", "edad": 27, "telefono": "3815551243", "email": "sgarcia@gmail.com"},
]

@app.get("/contactos")
def listarContactos():
    return contactos

@app.get("/contactos/{nombre}")
def contactoEspecifico(nombre: str):
    for contacto in contactos:
        if contacto["nombre"].lower() == nombre.lower():
            return contacto
    raise HTTPException(status_code=404, detail=f"Contacto '{nombre}' no encontrado")

