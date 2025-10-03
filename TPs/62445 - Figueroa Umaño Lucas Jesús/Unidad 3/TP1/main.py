from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from typing import List
import uvicorn

# Crear la aplicación FastAPI
app = FastAPI(
    title="Agenda de Contactos",
    description="Una API para mostrar contactos",
    version="1.0.0"
)

# Modelo de datos para un contacto
class Contacto(BaseModel):
    nombre: str
    apellido: str
    edad: int
    telefono: str
    email: EmailStr

# Datos estáticos en memoria - Lista de contactos hardcoded (mínimo 10)
contactos_db = [
    {
        "nombre": "Juan", "apellido": "Fernandez", "edad": 28, "telefono": "381-1234567", "email": "juanf@email.com"
    },
    {
        "nombre": "María", "apellido": "García", "edad": 34, "telefono": "381-2345678", "email": "maria.garcia@email.com"
    },
    {
        "nombre": "Carlos", "apellido": "López", "edad": 45, "telefono": "381-3456789", "email": "carlos.lopez@email.com"
    },
    {
        "nombre": "Ana", "apellido": "Martínez", "edad": 31, "telefono": "381-4567890", "email": "ana.martinez@email.com"
    },
    {
        "nombre": "Luis", "apellido": "Rodríguez", "edad": 27, "telefono": "381-5678901", "email": "luis.rodriguez@email.com"
    },
    {
        "nombre": "Laura", "apellido": "Fernández", "edad": 39, "telefono": "381-6789012", "email": "laura.fernandez@email.com"
    },
    {
        "nombre": "Diego", "apellido": "González", "edad": 42, "telefono": "381-7890123", "email": "diego.gonzalez@email.com"
    },
    {
        "nombre": "Sofía", "apellido": "Sánchez", "edad": 26, "telefono": "381-8901234", "email": "sofia.sanchez@email.com"
    },
    {
        "nombre": "Miguel", "apellido": "Torres", "edad": 35, "telefono": "381-9012345", "email": "miguel.torres@email.com"
    },
    {
        "nombre": "Carmen", "apellido": "Ruiz", "edad": 29, "telefono": "381-0123456", "email": "carmen.ruiz@email.com"
    },
    {
        "nombre": "Roberto", "apellido": "Jiménez", "edad": 38, "telefono": "381-1234098", "email": "roberto.jimenez@email.com"
    },
    {
        "nombre": "Isabel", "apellido": "Moreno", "edad": 33, "telefono": "381-2340987", "email": "isabel.moreno@email.com"
    }
]

# ENDPOINTS

@app.get("/")
async def mensaje_bienvenida():
    "Endpoint GET raíz que devuelve un mensaje de bienvenida"
    return {
        "mensaje": f"¡Bienvenido a la Agenda de Contactos!",
        "descripcion": app.description,
        "total_contactos": len(contactos_db),
        "endpoints_disponibles": {
            "GET /": "Mensaje de bienvenida",
            "GET /contactos": "Listar todos los contactos",
            "GET /contactos/{index}" : "Obtener contacto por índice"
            }
        }

@app.get("/contactos", response_model=List[Contacto])
async def listar_contactos():
    """Endpoint GET para listar todos los contactos estáticos en formato JSON"""
    if not contactos_db:
        raise HTTPException(status_code=404, detail="No se encontraron contactos")
    
    return contactos_db

@app.get("/contactos/{index}")
async def obtener_contacto_por_indice(index: int):
    """Endpoint adicional para obtener un contacto por índice (manejo de errores 404)"""
    try:
        if index < 0 or index >= len(contactos_db):
            raise HTTPException(status_code=404, detail=f"Contacto en índice {index} no encontrado")
        
        return contactos_db[index]
    except Exception as e:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")

# Manejo básico de errores para rutas no encontradas
@app.get("/error-demo")
async def demo_error():
    """Endpoint de demostración para manejo de errores"""
    raise HTTPException(status_code=404, detail="Esta es una demostración de manejo de errores")

# Ejecutar el servidor con uvicorn
if __name__ == "__main__":
    print("🚀 Iniciando servidor FastAPI...")
    print("📋 Agenda de Contactos cargada con", len(contactos_db), "contactos")
    print("🌐 Servidor disponible en: http://127.0.0.1:8000")
    print("📖 Documentación automática en: http://127.0.0.1:8000/docs")
    print("📚 Documentación alternativa en: http://127.0.0.1:8000/redoc")
    
    uvicorn.run(
        "main:app",  # Cambia "main" por el nombre de tu archivo Python
        host="127.0.0.1",
        port=8000,
        reload=True  # Recarga automática durante desarrollo
    )

@app.get("/contactos/buscar/{nombre}", response_model=List[Contacto])
async def buscar_contacto(nombre: str):
    resultados = [c for c in contactos_db if nombre.lower() in c["nombre"].lower()]
    if not resultados:
        raise HTTPException(status_code=404, detail=f"No se encontraron contactos con nombre '{nombre}'")
    return resultados
