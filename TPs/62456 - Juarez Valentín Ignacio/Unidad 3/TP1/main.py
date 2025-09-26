from fastapi import FastAPI, HTTPException

app = FastAPI()

contactos = [
    {"nombre": "Juan", "apellido": "Pérez", "edad": 30, "teléfono": "3815551234", "email": "jperez@gmail.com"},
    {"nombre": "José", "apellido": "Gómez", "edad": 25, "teléfono": "3815551235", "email": "jgomez@gmail.com"},
    {"nombre": "Ana", "apellido": "Martínez", "edad": 28, "teléfono": "3815551236", "email": "amartinez@gmail.com"},
    {"nombre": "Lucía", "apellido": "Rodríguez", "edad": 35, "teléfono": "3815551237", "email": "lrodriguez@gmail.com"},
    {"nombre": "Carlos", "apellido": "López", "edad": 40, "teléfono": "3815551238", "email": "clopez@gmail.com"},
    {"nombre": "María", "apellido": "García", "edad": 22, "teléfono": "3815551239", "email": "mgarcia@gmail.com"},
    {"nombre": "Pedro", "apellido": "Fernández", "edad": 31, "teléfono": "3815551240", "email": "pfernandez@gmail.com"},
    {"nombre": "Laura", "apellido": "Sánchez", "edad": 27, "teléfono": "3815551241", "email": "lsanchez@gmail.com"},
    {"nombre": "Diego", "apellido": "Torres", "edad": 29, "teléfono": "3815551242", "email": "dtorres@gmail.com"},
    {"nombre": "Sofía", "apellido": "Ruiz", "edad": 33, "teléfono": "3815551243", "email": "sruiz@gmail.com"}
]

@app.get("/")
def leer_raiz():
    return{"Mensaje: BIENVENIDOS A LA AGENDA DE CONTACTOS"}

@app.get("/contactos")
def lista_contactos():
    if not contactos:
        raise HTTPException(status_code=404, detail = "NO SE ENCONTRO EL CONTACTO")
    return contactos