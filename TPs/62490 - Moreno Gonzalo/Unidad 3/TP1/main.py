from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# Crear instancia de FastAPI
app = FastAPI(
    title="API de Contactos",
    description="Sistema de gestión de contactos básico",
    version="1.0.0"
)

# Lista de contactos hardcoded
contactos = [
    {
        "id": 1,
        "nombre": "Juan Pérez",
        "email": "juan.perez@email.com",
        "telefono": "+54 381 555-0101",
        "empresa": "Tech Solutions"
    },
    {
        "id": 2,
        "nombre": "María González",
        "email": "maria.gonzalez@email.com",
        "telefono": "+54 381 555-0102",
        "empresa": "Innovation Labs"
    },
    {
        "id": 3,
        "nombre": "Carlos Rodríguez",
        "email": "carlos.rodriguez@email.com",
        "telefono": "+54 381 555-0103",
        "empresa": "Digital Marketing"
    },
    {
        "id": 4,
        "nombre": "Ana Martínez",
        "email": "ana.martinez@email.com",
        "telefono": "+54 381 555-0104",
        "empresa": "Creative Design"
    },
    {
        "id": 5,
        "nombre": "Luis Fernández",
        "email": "luis.fernandez@email.com",
        "telefono": "+54 381 555-0105",
        "empresa": "Data Analytics"
    },
    {
        "id": 6,
        "nombre": "Laura Sánchez",
        "email": "laura.sanchez@email.com",
        "telefono": "+54 381 555-0106",
        "empresa": "Cloud Services"
    },
    {
        "id": 7,
        "nombre": "Diego Torres",
        "email": "diego.torres@email.com",
        "telefono": "+54 381 555-0107",
        "empresa": "Mobile Apps"
    },
    {
        "id": 8,
        "nombre": "Sofía López",
        "email": "sofia.lopez@email.com",
        "telefono": "+54 381 555-0108",
        "empresa": "AI Research"
    },
    {
        "id": 9,
        "nombre": "Martín Díaz",
        "email": "martin.diaz@email.com",
        "telefono": "+54 381 555-0109",
        "empresa": "Cybersecurity"
    },
    {
        "id": 10,
        "nombre": "Valentina Romero",
        "email": "valentina.romero@email.com",
        "telefono": "+54 381 555-0110",
        "empresa": "Blockchain Tech"
    },
    {
        "id": 11,
        "nombre": "Facundo Silva",
        "email": "facundo.silva@email.com",
        "telefono": "+54 381 555-0111",
        "empresa": "E-commerce Solutions"
    },
    {
        "id": 12,
        "nombre": "Camila Acosta",
        "email": "camila.acosta@email.com",
        "telefono": "+54 381 555-0112",
        "empresa": "Digital Consulting"
    }
]


# Endpoint raíz - Mensaje de bienvenida
@app.get("/")
async def root():
    """
    Endpoint de bienvenida del sistema
    """
    return {
        "mensaje": "¡Bienvenido al Sistema de Gestión de Contactos!",
        "version": "1.0.0",
        "endpoints": {
            "listar_contactos": "/contactos",
            "buscar_por_id": "/contactos/{id}",
            "documentacion": "/docs"
        }
    }


# Endpoint para listar todos los contactos
@app.get("/contactos")
async def listar_contactos():
    """
    Obtiene la lista completa de contactos
    """
    return {
        "total": len(contactos),
        "contactos": contactos
    }


# Endpoint para buscar contacto por ID (con manejo de errores)
@app.get("/contactos/{contacto_id}")
async def obtener_contacto(contacto_id: int):
    """
    Obtiene un contacto específico por su ID
    """
    contacto = next((c for c in contactos if c["id"] == contacto_id), None)
    
    if contacto is None:
        raise HTTPException(
            status_code=404,
            detail=f"Contacto con ID {contacto_id} no encontrado"
        )
    
    return contacto


# Manejador personalizado de errores 404
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Recurso no encontrado",
            "mensaje": "La ruta solicitada no existe en el servidor",
            "ruta": str(request.url)
        }
    )


# Manejador de errores generales
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Error interno del servidor",
            "mensaje": str(exc)
        }
    )


# Ejecutar el servidor
if __name__ == "__main__":
    print("🚀 Iniciando servidor FastAPI...")
    print("📍 Servidor disponible en: http://127.0.0.1:8000")
    print("📖 Documentación interactiva: http://127.0.0.1:8000/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )