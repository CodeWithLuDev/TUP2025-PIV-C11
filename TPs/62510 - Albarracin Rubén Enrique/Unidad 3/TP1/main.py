from fastapi import FastAPI, HTTPException
from typing import List, Dict
import uvicorn

# Crear instancia de FastAPI
app = FastAPI(
    title="Agenda de Contactos API",
    description="API para gestionar una agenda de contactos",
    version="1.0.0"
)

# Estructura de datos - Lista de contactos en memoria
contactos: List[Dict[str, any]] = [
    {
        "nombre": "Juan",
        "apellido": "Pérez",
        "edad": 30,
        "teléfono": "3815551234",
        "email": "jperez@gmail.com"
    },
    {
        "nombre": "José",
        "apellido": "Gómez",
        "edad": 25,
        "teléfono": "3815551235",
        "email": "jgomez@gmail.com"
    },
    {
        "nombre": "María",
        "apellido": "Rodríguez",
        "edad": 28,
        "teléfono": "3815551236",
        "email": "mrodriguez@gmail.com"
    },
    {
        "nombre": "Ana",
        "apellido": "Martínez",
        "edad": 32,
        "teléfono": "3815551237",
        "email": "amartinez@gmail.com"
    },
    {
        "nombre": "Carlos",
        "apellido": "López",
        "edad": 27,
        "teléfono": "3815551238",
        "email": "clopez@gmail.com"
    },
    {
        "nombre": "Laura",
        "apellido": "Fernández",
        "edad": 35,
        "teléfono": "3815551239",
        "email": "lfernandez@gmail.com"
    },
    {
        "nombre": "Diego",
        "apellido": "González",
        "edad": 29,
        "teléfono": "3815551240",
        "email": "dgonzalez@gmail.com"
    },
    {
        "nombre": "Sofía",
        "apellido": "Sánchez",
        "edad": 26,
        "teléfono": "3815551241",
        "email": "ssanchez@gmail.com"
    },
    {
        "nombre": "Miguel",
        "apellido": "Torres",
        "edad": 31,
        "teléfono": "3815551242",
        "email": "mtorres@gmail.com"
    },
    {
        "nombre": "Valentina",
        "apellido": "Ramírez",
        "edad": 24,
        "teléfono": "3815551243",
        "email": "vramirez@gmail.com"
    },
    {
        "nombre": "Lucas",
        "apellido": "Flores",
        "edad": 33,
        "teléfono": "3815551244",
        "email": "lflores@gmail.com"
    }
]


# Endpoint raíz - Mensaje de bienvenida
@app.get("/")
async def root():
    """
    Endpoint raíz que devuelve un mensaje de bienvenida.
    """
    return {"mensaje": "Bienvenido a la Agenda de Contactos API"}


# Endpoint para listar todos los contactos
@app.get("/contactos")
async def obtener_contactos():
    """
    Devuelve la lista completa de contactos.
    """
    if not contactos:
        raise HTTPException(
            status_code=404,
            detail="No hay contactos disponibles en la agenda"
        )
    return contactos


# Endpoint para obtener un contacto por índice
@app.get("/contactos/{contacto_id}")
async def obtener_contacto(contacto_id: int):
    """
    Devuelve un contacto específico por su índice.
    """
    if contacto_id < 0 or contacto_id >= len(contactos):
        raise HTTPException(
            status_code=404,
            detail=f"Contacto con ID {contacto_id} no encontrado"
        )
    return contactos[contacto_id]


# Endpoint de salud del servidor
@app.get("/health")
async def health_check():
    """
    Endpoint para verificar el estado del servidor.
    """
    return {
        "status": "OK",
        "total_contactos": len(contactos)
    }


# Punto de entrada para ejecutar el servidor
if __name__ == "__main__":
    print("=== AGENDA DE CONTACTOS API ===")
    print("Iniciando servidor...")
    print("Visita: http://127.0.0.1:8000/")
    print("Documentación: http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)