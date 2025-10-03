from fastapi import FastAPI, HTTPException

app = FastAPI()

# Agenda estática en memoria
contactos = [
    {"id": 1, "nombre": "Juan", "apellido": "Pérez", "edad": 30, "telefono": "123456789", "email": "juan@example.com"},
    {"id": 2, "nombre": "Ana", "apellido": "Gómez", "edad": 25, "telefono": "987654321", "email": "ana@example.com"},
    {"id": 3, "nombre": "Luis", "apellido": "Martínez", "edad": 40, "telefono": "555111222", "email": "luis@example.com"},
    {"id": 4, "nombre": "Carla", "apellido": "López", "edad": 35, "telefono": "444555666", "email": "carla@example.com"},
    {"id": 5, "nombre": "Pedro", "apellido": "Ramírez", "edad": 28, "telefono": "222333444", "email": "pedro@example.com"},
    {"id": 6, "nombre": "Laura", "apellido": "Fernández", "edad": 32, "telefono": "666777888", "email": "laura@example.com"},
    {"id": 7, "nombre": "Sofía", "apellido": "Torres", "edad": 27, "telefono": "111222333", "email": "sofia@example.com"},
    {"id": 8, "nombre": "Diego", "apellido": "Castro", "edad": 29, "telefono": "333444555", "email": "diego@example.com"},
    {"id": 9, "nombre": "María", "apellido": "Suárez", "edad": 45, "telefono": "777888999", "email": "maria@example.com"},
    {"id": 10, "nombre": "Andrés", "apellido": "Morales", "edad": 38, "telefono": "999000111", "email": "andres@example.com"}
]

# Endpoint raíz
@app.get("/")
def inicio():
    return {"mensaje": "Bienvenido a la Agenda de Contactos"}

# Endpoint para listar todos los contactos
@app.get("/contactos")
def listar_contactos():
    return {"contactos": contactos}

# Endpoint para obtener un contacto por ID
@app.get("/contactos/{contacto_id}")
def obtener_contacto(contacto_id: int):
    for c in contactos:
        if c["id"] == contacto_id:
            return c
    raise HTTPException(status_code=404, detail="Contacto no encontrado")
