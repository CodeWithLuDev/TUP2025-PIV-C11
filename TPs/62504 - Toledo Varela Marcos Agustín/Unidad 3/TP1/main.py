from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI (
    title="Agenda API",
    description="Una API básica desarrollada con *FastAPI* que funciona como una agenda de contactos.",
    version="1.0"
)

#Lista de contactos (mínimo 10)

CONTACTOS = [
    
    {"nombre": "Juan", "apellido": "Pérez", "edad": 30, "teléfono": "3815551234", "email": "jperez@gmail.com"},
    {"nombre": "José", "apellido": "Gómez", "edad": 25, "teléfono": "3815551235", "email": "jgomez@gmail.com"},
    {"nombre": "Agustin", "apellido":"Toledo", "edad": 24, "teléfono":"3865-331586", "email": "agustintoledo@gmail.com"},
    {"nombre": "Marcos", "apellido": "Varela", "edad": 20, "teléfono": "334235444", "email": "marcosvarela@gmail.com"},
    {"nombre": "Carlos", "apellido": "Vera", "edad": 38, "teléfono": "334235444", "email": "car_ve@gmail.com"},
    {"nombre": "Diego", "apellido": "Martínez", "edad": 50, "teléfono": "45654634", "email": "diego@example.com"},
    {"nombre": "Valentina", "apellido": "Sánchez", "edad": 27, "teléfono": "34534567", "email": "valentina@example.com"},
    {"nombre": "Sofía", "apellido": "Gómez", "edad": 41, "teléfono": "87656856", "email": "sofia@example.com"},
    {"nombre": "Martín", "apellido": "López", "edad": 36, "teléfono": "2547457", "email": "martin@example.com"},
    {"nombre": "Nicolás", "apellido": "Díaz", "edad": 33, "teléfono": "45757543", "email": "nicolas@example.com"}
    
]

# Endpoint raíz
@app.get("/")
def raiz():
    return {"mensaje": "Bienvenido a la Agenda de Contactos API"}

# Endpoint para listar todos los contactos
@app.get("/contactos")
def listar_contactos():
    return CONTACTOS

# Endpoint para acceder a un contacto por índice
@app.get("/contactos/{indice}")
def obtener_contacto(indice: int):
    if 0 <= indice < len(CONTACTOS):
        return CONTACTOS[indice]
    raise HTTPException(status_code=404, detail="Contacto no encontrado")

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
