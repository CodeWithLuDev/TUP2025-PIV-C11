from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any
import uvicorn

# Crear la instancia de FastAPI
app = FastAPI(
    title="Agenda de Contactos API",
    description="API básica para gestionar una agenda de contactos",
    version="1.0.0"
)

# Estructura de datos estática - Lista de contactos en memoria
contactos_db: List[Dict[str, Any]] = [
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
        "apellido": "González",
        "edad": 28,
        "teléfono": "3815551236",
        "email": "mgonzalez@gmail.com"
    },
    {
        "nombre": "Carlos",
        "apellido": "Rodríguez",
        "edad": 35,
        "teléfono": "3815551237",
        "email": "crodriguez@hotmail.com"
    },
    {
        "nombre": "Ana",
        "apellido": "Martínez",
        "edad": 22,
        "teléfono": "3815551238",
        "email": "amartinez@yahoo.com"
    },
    {
        "nombre": "Pedro",
        "apellido": "López",
        "edad": 40,
        "teléfono": "3815551239",
        "email": "plopez@gmail.com"
    },
    {
        "nombre": "Laura",
        "apellido": "Fernández",
        "edad": 32,
        "teléfono": "3815551240",
        "email": "lfernandez@outlook.com"
    },
    {
        "nombre": "Diego",
        "apellido": "Sánchez",
        "edad": 27,
        "teléfono": "3815551241",
        "email": "dsanchez@gmail.com"
    },
    {
        "nombre": "Sofía",
        "apellido": "Torres",
        "edad": 29,
        "teléfono": "3815551242",
        "email": "storres@hotmail.com"
    },
    {
        "nombre": "Roberto",
        "apellido": "Morales",
        "edad": 45,
        "teléfono": "3815551243",
        "email": "rmorales@gmail.com"
    },
    {
        "nombre": "Valentina",
        "apellido": "Herrera",
        "edad": 24,
        "teléfono": "3815551244",
        "email": "vherrera@yahoo.com"
    },
    {
        "nombre": "Alejandro",
        "apellido": "Castro",
        "edad": 38,
        "teléfono": "3815551245",
        "email": "acastro@outlook.com"
    }
]

@app.get("/")
async def root():
    """
    Endpoint raíz que devuelve un mensaje de bienvenida
    """
    return {"mensaje": "Bienvenido a la Agenda de Contactos API"}

@app.get("/contactos")
async def obtener_contactos():
    """
    Endpoint para obtener todos los contactos de la agenda
    """
    try:
        if not contactos_db:
            raise HTTPException(status_code=404, detail="No se encontraron contactos en la agenda")
        
        return contactos_db
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@app.get("/contactos/{indice}")
async def obtener_contacto_por_indice(indice: int):
    """
    Endpoint para obtener un contacto específico por su índice
    """
    try:
        if indice < 0 or indice >= len(contactos_db):
            raise HTTPException(
                status_code=404, 
                detail=f"Contacto con índice {indice} no encontrado. Índices válidos: 0-{len(contactos_db)-1}"
            )
        
        return contactos_db[indice]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@app.get("/health")
async def health_check():
    """
    Endpoint para verificar el estado del servidor
    """
    return {
        "status": "OK", 
        "mensaje": "El servidor está funcionando correctamente",
        "total_contactos": len(contactos_db)
    }

# Manejo de errores 404 personalizado
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {
        "error": "Recurso no encontrado",
        "mensaje": "La ruta solicitada no existe",
        "rutas_disponibles": [
            "/",
            "/contactos",
            "/contactos/{indice}",
            "/health"
        ]
    }

if __name__ == "__main__":
    print("=== AGENDA DE CONTACTOS API ===")
    print("Iniciando servidor...")
    print("Accede a: http://127.0.0.1:8000")
    print("Documentación: http://127.0.0.1:8000/docs")
    
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )