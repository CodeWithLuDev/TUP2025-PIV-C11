from fastapi import FastAPI, HTTPException

app = FastAPI()

# Lista de 10 contactos
contactos =[
    {"id": 1, "nombre": "Julieta", "apellido": "Montoya", "edad": 29, "telefono": "3816554371", "email": "julieta.montoya@example.com"},
    {"id": 2, "nombre": "Gael", "apellido": "Delgado", "edad": 41, "telefono": "3816554372", "email": "gael.delgado@example.com"},
    {"id": 3, "nombre": "Romina", "apellido": "Salvatierra", "edad": 34, "telefono": "3816554373", "email": "romina.salva@example.com"},
    {"id": 4, "nombre": "Lisandro", "apellido": "Ferrari", "edad": 27, "telefono": "3816554374", "email": "lisandro.f@example.com"},
    {"id": 5, "nombre": "Valeria", "apellido": "Kawasaki", "edad": 38, "telefono": "3816554375", "email": "valeria.k@example.com"},
    {"id": 6, "nombre": "Amparo", "apellido": "González", "edad": 45, "telefono": "3816554376", "email": "amparo.g@example.com"},
    {"id": 7, "nombre": "Thiago", "apellido": "Maldonado", "edad": 22, "telefono": "3816554377", "email": "thiago.m@example.com"},
    {"id": 8, "nombre": "Ilya", "apellido": "Petrov", "edad": 50, "telefono": "3816554378", "email": "ilya.petrov@example.com"},
    {"id": 9, "nombre": "Lucrecia", "apellido": "Campos", "edad": 31, "telefono": "3816554379", "email": "lucrecia.c@example.com"},
    {"id": 10, "nombre": "Abril", "apellido": "Sánchez", "edad": 26, "telefono": "3816554380", "email": "abril.sanchez@example.com"}
]


@app.get("/")
def index():
    return {"mensaje": "Bienvenido a la lista de Contactos "}

@app.get("/contactos")
def lista_agenda():
    return contactos

@app.get("/contactos/{contacto_id}")
def obtener_contacto_unico(contacto_id: int):
    for contacto in contactos:
        if contacto["id"] == contacto_id:
            return c
    raise HTTPException(status_code=404, detail="Contacto no existente")