from fastapi import FastAPI, HTTPException

app = FastAPI()

contactos = [
    {"apellido": "Albornoz", "nombre": "Benjamin", "edad": 20, "telefono": "3815551234", "email": "b.alb@gmail.com"},
    {"apellido": "Paez", "nombre": "Gonzalo", "edad": 20, "telefono": "3865566889", "email": "gpaez@gmail.com"},
]

@app.get("/")
def inicio():
    return {"mensaje": "Bienvenido a la Agenda de Contactos API"}

# 2. Listar todos los contactos
@app.get("/contactos")
def listar_contactos():
    return contactos

@app.get("/contactos/nombres-telefonos")
def nombres_y_telefonos():
    return [
        {"nombre_completo": f"{c['nombre']} {c['apellido']}", "telefono": c["telefono"]}
        for c in contactos
    ]

@app.get("/contactos/{contacto_id}")
def obtener_contacto(contacto_id: int):
    if 0 <= contacto_id < len(contactos):
        return contactos[contacto_id]
    raise HTTPException(status_code=404, detail="Contacto no encontrado")
