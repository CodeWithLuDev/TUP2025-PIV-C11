from fastapi import FastAPI, HTTPException

# Crear la instancia de la aplicación FastAPI
app = FastAPI(
    title="Agenda de Contactos API",
    description="Una API simple para manejar una agenda de contactos estática.",
    version="1.0.0"
)

# Lista de contactos estática (hardcoded) con al menos 10 entradas
contactos = [
    {"nombre": "Juan", "apellido": "Pérez", "edad": 30, "teléfono": "3815551234", "email": "jperez@gmail.com"},
    {"nombre": "José", "apellido": "Gómez", "edad": 25, "teléfono": "3815551235", "email": "jgomez@gmail.com"},
    {"nombre": "María", "apellido": "López", "edad": 28, "teléfono": "3815551236", "email": "mlopez@gmail.com"},
    {"nombre": "Ana", "apellido": "Martínez", "edad": 35, "teléfono": "3815551237", "email": "amartinez@gmail.com"},
    {"nombre": "Carlos", "apellido": "Rodríguez", "edad": 40, "teléfono": "3815551238", "email": "crodriguez@gmail.com"},
    {"nombre": "Laura", "apellido": "Fernández", "edad": 22, "teléfono": "3815551239", "email": "lfernandez@gmail.com"},
    {"nombre": "Pedro", "apellido": "García", "edad": 45, "teléfono": "3815551240", "email": "pgarcia@gmail.com"},
    {"nombre": "Sofía", "apellido": "Hernández", "edad": 29, "teléfono": "3815551241", "email": "shernandez@gmail.com"},
    {"nombre": "Miguel", "apellido": "Díaz", "edad": 33, "teléfono": "3815551242", "email": "mdiaz@gmail.com"},
    {"nombre": "Elena", "apellido": "Ruiz", "edad": 27, "teléfono": "3815551243", "email": "eruiz@gmail.com"}
]

# Endpoint GET para la raíz (/)
@app.get("/")
def leer_raiz():
    return {"mensaje": "Bienvenido a la Agenda de Contactos API"}

# Endpoint GET para listar todos los contactos
@app.get("/contactos")
def obtener_contactos():
    if not contactos:
        # Manejo básico de error si la lista está vacía (aunque no debería ocurrir)
        raise HTTPException(status_code=404, detail="No se encontraron contactos")
    return contactos

# Manejador global para errores 404 (personalizado, opcional pero recomendado para manejo básico)
@app.exception_handler(404)
async def manejador_404(request, exc):
    return {"error": "Recurso no encontrado. Por favor, verifica la URL."}