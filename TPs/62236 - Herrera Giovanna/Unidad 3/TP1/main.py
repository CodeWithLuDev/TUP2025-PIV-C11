from fastapi import FastAPI, HTTPException
app = FastAPI ()

# LISTA DE CONTACTOS

contactos = [
    {"nombre": "Juan Cruz", "apellido": "Martinez", "edad": 19, "telefono": "3863889014", "email": "juancruz192@gmail.com"},
    {"nombre": "Mateo", "apellido": "Herrera", "edad": 23, "telefono": "3863442174", "email": "mateoh33@gmail.com"},
    {"nombre": "Sabina", "apellido": "Villarreal", "edad": 20, "telefono": "3863435492", "email": "sabimaite12@gmail.com"},
    {"nombre": "Sofia", "apellido": "Rivadeo", "edad": 42, "telefono": "3812443977", "email": "drivadeo@gmail.com"},
    {"nombre": "Giovanna", "apellido": "Herrera", "edad": 20, "telefono": "3863431859", "email": "giooherreera@gmail.com"},
    {"nombre": "Oscar", "apellido": "Chico", "edad": 30, "telefono": "3863511430", "email": "oscar258h@gmail.com"},
    {"nombre": "Luis", "apellido": "Robles", "edad": 22, "telefono": "3863440697", "email": "luisr22@gmail.com"},
    {"nombre": "Guadalupe", "apellido": "Lastra", "edad": 21, "telefono": "3863503142", "email": "lastraG@gmail.com"},
    {"nombre": "Abril", "apellido": "Luis", "edad": 38, "telefono": "3863889019", "email": "LuisPris22@gmail.com"},
    {"nombre": "Lucas", "apellido": "Pedraza", "edad": 26, "telefono": "3863841014", "email": "pedraza5@gmail.com"},
]

@app.get("/")
def inicio():
    return {"mensaje": "Bienvenidos a la Agenda de Contactos API"}

# Listar todos los contactos
@app.get("/contactos")
def listar_contactos():
    return contactos 

#Contacto por nombre (errores)
@app.get("/contactos/{nombre}")
def buscar_contacto(nombre: str):
    for contacto in contactos:
        if contacto["nombre"].lower() == nombre.lower():
            return contacto

    raise HTTPException(status_code=404, detail="Contacto no encontrado")