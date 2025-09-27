from fastapi import FastAPI, HTTPException

app = FastAPI()

# Lista de 10 contactos
contactos = [
    {"id": 1, "nombre": "Ariadna", "apellido": "Soler", "edad": 29, "telefono": "3816554321", "email": "ariadna.soler@example.com"},
    {"id": 2, "nombre": "Isandro", "apellido": "Quintero", "edad": 41, "telefono": "3816554322", "email": "isandro.q@example.com"},
    {"id": 3, "nombre": "Mireya", "apellido": "Alcocer", "edad": 34, "telefono": "3816554323", "email": "mireya.alc@example.com"},
    {"id": 4, "nombre": "Breno", "apellido": "Tavares", "edad": 27, "telefono": "3816554324", "email": "breno.tavares@example.com"},
    {"id": 5, "nombre": "Ornella", "apellido": "Ichikawa", "edad": 38, "telefono": "3816554325", "email": "ornella.i@example.com"},
    {"id": 6, "nombre": "Leocadia", "apellido": "Murillo", "edad": 45, "telefono": "3816554326", "email": "leocadia.m@example.com"},
    {"id": 7, "nombre": "Khalil", "apellido": "Zamarripa", "edad": 22, "telefono": "3816554327", "email": "khalil.z@example.com"},
    {"id": 8, "nombre": "Vasili", "apellido": "Korolenko", "edad": 50, "telefono": "3816554328", "email": "vasili.k@example.com"},
    {"id": 9, "nombre": "Candelaria", "apellido": "Urbano", "edad": 31, "telefono": "3816554329", "email": "candelaria.u@example.com"},
    {"id": 10, "nombre": "Nayeli", "apellido": "Ortíz", "edad": 26, "telefono": "3816554330", "email": "nayeli.ortiz@example.com"},
]

@app.get("/")
def raiz():
    return {"mensaje": "Bienvenido a la Agenda de Contactos API"}

@app.get("/contactos")
def listar_contactos():
    return contactos

@app.get("/contactos/{contacto_id}")
def obtener_contacto(contacto_id: int):
    for c in contactos:
        if c["id"] == contacto_id:
            return c
    raise HTTPException(status_code=404, detail="Contacto no encontrado")
