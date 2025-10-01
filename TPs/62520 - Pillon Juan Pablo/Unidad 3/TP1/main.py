from fastapi import FastAPI, HTTPException

app = FastAPI()

# 🧱 Clase Contacto
class Contacto:
    def __init__(self, nombre: str, apellido: str, edad: int, telefono: str, email: str):
        self.nombre = nombre
        self.apellido = apellido
        self.edad = edad
        self.telefono = telefono
        self.email = email

    def to_dict(self):
        return {
            "nombre": self.nombre,
            "apellido": self.apellido,
            "edad": self.edad,
            "teléfono": self.telefono,
            "email": self.email
        }

# 📋 Lista de contactos hardcoded
agenda = [
    Contacto("Juan", "Pérez", 30, "3815551234", "jperez@gmail.com"),
    Contacto("José", "Gómez", 25, "3815551235", "jgomez@gmail.com"),
    Contacto("Lucía", "Fernández", 33, "3815551236", "lucia.fernandez@gmail.com"),
    Contacto("Carlos", "Gutiérrez", 45, "3815551237", "carlosg@empresa.com"),
    Contacto("Valentina", "Torres", 40, "3815551238", "valentina.torres@freelance.com"),
    Contacto("Camila", "Suárez", 27, "3815551239", "camisuarez@outlook.com"),
    Contacto("Bruno", "Peralta", 31, "3815551240", "bruno.peralta@devs.ar"),
    Contacto("Martín", "Alonso", 19, "3815551241", "martinalonso@estudiante.edu"),
    Contacto("Federico", "López", 50, "3815551242", "fede.lopez@correo.com"),
    Contacto("Sofía", "Ramírez", 28, "3815551243", "sofia.ramirez@gmail.com"),
]

# 🌐 Endpoint raíz
@app.get("/")
def read_root():
    return {"mensaje": "Bienvenido a la Agenda de Contactos API"}

# 📂 Endpoint para listar contactos
@app.get("/contactos")
def listar_contactos():
    return [c.to_dict() for c in agenda]

# ⚠️ Endpoint para obtener contacto por índice (con manejo de error)
@app.get("/contactos/{indice}")
def obtener_contacto(indice: int):
    if indice < 0 or indice >= len(agenda):
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    return agenda[indice].to_dict()
