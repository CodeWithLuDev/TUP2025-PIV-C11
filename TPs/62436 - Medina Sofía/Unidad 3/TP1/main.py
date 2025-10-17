from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any
import uvicorn

app = FastAPI()

contactos: List[Dict[str, Any]] = [
    {
        "nombre": "Juan",
        "apellido": "Medina",
        "edad": 22,
        "telefono": 3865258579,
        "email": "juanm@gmail.com"
    },
    {
        "nombre": "Ana",
        "apellido": "Ruiz",
        "edad": 65,
        "telefono": 3865972461,
        "email": "anaru@gmail.com"
    },
    {
        "nombre": "María",
        "apellido": "López",
        "edad": 28,
        "teléfono": "3815551236",
        "email": "mlopez@gmail.com"
    },
    {
         "nombre": "Carlos",
        "apellido": "Rodríguez",
        "edad": 27,
        "teléfono": "3815551238",
        "email": "crodriguez@gmail.com"
    },
    {
        "nombre": "María",
        "apellido": "López",
        "edad": 28,
        "teléfono": "3815551236",
        "email": "mlopez@gmail.com"

    },
    {
        "nombre": "Laura",
        "apellido": "Fernández",
        "edad": 29,
        "teléfono": "3815551239",
        "email": "lfernandez@gmail.com"
    },
    {
        "nombre": "Sofía",
        "apellido": "Ramírez",
        "edad": 24,
        "teléfono": "3815551241",
        "email": "sramirez@gmail.com"
    },
    {
        "nombre": "Valentina",
        "apellido": "Flores",
        "edad": 26,
        "teléfono": "3815551243",
        "email": "vflores@gmail.com"
    },
    {
        "nombre": "Camila",
        "apellido": "Díaz",
        "edad": 22,
        "teléfono": "3815551245",
        "email": "cdiaz@gmail.com"
    },
    {
        "nombre": "Pedro",
        "apellido": "Sánchez",
        "edad": 35,
        "teléfono": "3815551240",
        "email": "psanchez@gmail.com"
    }
]

@app.get("/")
def raiz():
    return {"mensaje": "Bienvenido a la Agenda de Contactos API"}

@app.get("/contactos")
def obtener_contactos():
    if not contactos:
        raise HTTPException(status_code=404, detail="No se encontraron contactos en la agenda")
    return contactos

# Manejo de error 404 para rutas no encontradas
@app.get("/{ruta_invalida:path}")
def ruta_no_encontrada(ruta_invalida: str):
    raise HTTPException(status_code=404, detail=f"La ruta '/{ruta_invalida}' no existe")

if __name__ == "__main__":
    print("=== AGENDA DE CONTACTOS API ===")
    print("Iniciando servidor...")
    print("Visita: http://127.0.0.1:8000/")
    print("Documentación interactiva: http://127.0.0.1:8000/docs")
   
    uvicorn.run(
        "main:app",
        host="127.0.0.1", 
        port=8000, 
        reload=True
    )