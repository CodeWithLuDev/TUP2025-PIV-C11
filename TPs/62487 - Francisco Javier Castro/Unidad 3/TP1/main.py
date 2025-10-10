from fastapi import FastAPI, HTTPException
import uvicorn


app = FastAPI(title="Agenda de Contactos API")


contactos = [
    {"nombre": "Franco", "apellido": "Bustos", "edad": 22, "teléfono": "3815001111", "email": "francobustos@gmail.com"},
    {"nombre": "Valentina", "apellido": "Ríos", "edad": 27, "teléfono": "3816002222", "email": "valentinar@gmail.com"},
    {"nombre": "Agustín", "apellido": "Moreno", "edad": 29, "teléfono": "3814003333", "email": "amoreno@gmail.com"},
    {"nombre": "Milagros", "apellido": "Vega", "edad": 25, "teléfono": "3815004444", "email": "milavega@gmail.com"},
    {"nombre": "Tomás", "apellido": "Herrera", "edad": 30, "teléfono": "3815555555", "email": "tomherrera@gmail.com"},
    {"nombre": "Brenda", "apellido": "Correa", "edad": 24, "teléfono": "3815116666", "email": "bcorrea@gmail.com"},
    {"nombre": "Ezequiel", "apellido": "Luna", "edad": 28, "teléfono": "3815227777", "email": "ezeqluna@gmail.com"},
    {"nombre": "Martina", "apellido": "Campos", "edad": 26, "teléfono": "3815338888", "email": "martinacampos@gmail.com"},
    {"nombre": "Julián", "apellido": "Paz", "edad": 31, "teléfono": "3815449999", "email": "julianpaz@gmail.com"},
    {"nombre": "Candela", "apellido": "Romero", "edad": 23, "teléfono": "3815550000", "email": "candela.romero@gmail.com"}
]

@app.get("/")
def inicio():
    return {"mensaje": "Bienvenido a la Agenda de Contactos API"}


@app.get("/contactos")
def listar_contactos():
    return contactos


@app.get("/contactos/{nombre}")
def buscar_contacto(nombre: str):
    for contacto in contactos:
        if contacto["nombre"].lower() == nombre.lower():
            return contacto

    raise HTTPException(status_code=404, detail="Contacto no encontrado")


if __name__ == "__main__":
    print("AGENDA DE CONTACTOS API")
    print("Servidor corriendo en: http://127.0.0.1:8000")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
