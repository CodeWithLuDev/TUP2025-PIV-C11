from fastapi import FastAPI, HTTPException

app = FastAPI()


agenda = [
    {"nombre": "Juan", "apellido": "Pérez", "edad": 30, "telefono": "111-111", "email": "juan@mail.com"},
    {"nombre": "Ana", "apellido": "García", "edad": 25, "telefono": "222-222", "email": "ana@mail.com"},
    {"nombre": "Luis", "apellido": "Martínez", "edad": 40, "telefono": "333-333", "email": "luis@mail.com"},
    {"nombre": "María", "apellido": "López", "edad": 28, "telefono": "444-444", "email": "maria@mail.com"},
    {"nombre": "Pedro", "apellido": "Sánchez", "edad": 35, "telefono": "555-555", "email": "pedro@mail.com"},
    {"nombre": "Lucía", "apellido": "Fernández", "edad": 22, "telefono": "666-666", "email": "lucia@mail.com"},
    {"nombre": "Carlos", "apellido": "Gómez", "edad": 45, "telefono": "777-777", "email": "carlos@mail.com"},
    {"nombre": "Sofía", "apellido": "Díaz", "edad": 29, "telefono": "888-888", "email": "sofia@mail.com"},
    {"nombre": "Diego", "apellido": "Ruiz", "edad": 33, "telefono": "999-999", "email": "diego@mail.com"},
    {"nombre": "Valeria", "apellido": "Torres", "edad": 27, "telefono": "101-101", "email": "valeria@mail.com"}
]


@app.get("/")
def read_root():
    return {"mensaje": "Bienvenido a la Agenda de Contactos"}


@app.get("/contactos")
def get_contactos():
    return agenda

@app.get("/contactos/{contacto_id}")
def get_contacto(contacto_id: int):
    if 0 <= contacto_id < len(agenda):
        return agenda[contacto_id]
    else:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
