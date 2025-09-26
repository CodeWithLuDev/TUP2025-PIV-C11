from fastapi import FastAPI, HTTPException

# Crear la aplicación FastAPI
app = FastAPI(title="Agenda de Contactos API")

# Datos estáticos en memoria (mínimo 10 contactos)
contactos = [
    {"nombre": "Juan", "apellido": "Brizuela", "edad": 30, "teléfono": "3815551234", "email": "jperez@gmail.com"},
    {"nombre": "Benjamin", "apellido": "Albornoz", "edad": 20, "teléfono": "3815551235", "email": "jgomez@gmail.com"},
    {"nombre": "Gonzalo", "apellido": "Paez", "edad": 20, "teléfono": "3815551236", "email": "mlopez@gmail.com"},
]

# Endpoint raíz
@app.get("/")
def read_root():
    return {"mensaje": "Bienvenido a la Agenda de Contactos API"}

# Endpoint para listar todos los contactos
@app.get("/contactos")
def listar_contactos():
    return contactos

# Endpoint para buscar un contacto por nombre
@app.get("/contactos/{nombre}")
def buscar_contacto(nombre: str):
    resultado = [c for c in contactos if c["nombre"].lower() == nombre.lower()]
    if not resultado:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    return resultado[0]
