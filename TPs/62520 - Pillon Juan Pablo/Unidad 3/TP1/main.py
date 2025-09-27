from fastapi import FastAPI, HTTPException

app = FastAPI()

agenda = [
    {"nombre": "Juan", "apellido": "Pérez", "edad": 30, "teléfono": "3815551234", "email": "jperez@gmail.com"},
    {"nombre": "José", "apellido": "Gómez", "edad": 25, "teléfono": "3815551235", "email": "jgomez@gmail.com"},
    {"nombre": "Nahuel", "apellido": "Mendoza", "edad": 36, "telefono": "123456789", "email": "nahuel@ejemplo.com"},
    {"nombre": "Diego", "apellido": "Juarez", "edad": 43, "telefono": "987654321", "email": "d1ego@napoli.com"},
    {"nombre": "Lionel", "apellido": "Messi", "edad": 36, "telefono": "123456789", "email": "messi@afa.com"},
    {"nombre": "Diego", "apellido": "Maradona", "edad": 60, "telefono": "987654321", "email": "d10s@napoli.com"},
    {"nombre": "Pablo", "apellido": "Milouan", "edad": 22, "telefono": "555123456", "email": "pablo@tup.com"},
    {"nombre": "Sofía", "apellido": "Ramírez", "edad": 28, "telefono": "341678900", "email": "sofia.ramirez@gmail.com"},
    {"nombre": "Carlos", "apellido": "Gutiérrez", "edad": 45, "telefono": "351112233", "email": "carlosg@empresa.com"},
    {"nombre": "Lucía", "apellido": "Fernández", "edad": 33, "telefono": "261445566", "email": "lucia.fernandez@yahoo.com"},
    {"nombre": "Martín", "apellido": "Alonso", "edad": 19, "telefono": "381998877", "email": "martinalonso@estudiante.edu"},
    {"nombre": "Valentina", "apellido": "Torres", "edad": 40, "telefono": "11-22334455", "email": "valentina.torres@freelance.com"},
    {"nombre": "Federico", "apellido": "López", "edad": 50, "telefono": "0341-667788", "email": "fede.lopez@correo.com"},
    {"nombre": "Camila", "apellido": "Suárez", "edad": 27, "telefono": "0261-334455", "email": "camisuarez@outlook.com"},
    {"nombre": "Bruno", "apellido": "Peralta", "edad": 31, "telefono": "0381-112233", "email": "bruno.peralta@devs.ar"},
]

    # ... agregá más contactos acá



@app.get("/")
def read_root():
    return {"mensaje": "Bienvenido a la Agenda de Contactos"}

@app.get("/contactos")
def listar_contactos():
    return {"contactos": agenda}

from fastapi import HTTPException

@app.get("/contactos/{indice}")
def obtener_contacto(indice: int):
    if indice < 0 or indice >= len(agenda):
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    return agenda[indice]
