from fastapi import FastAPI, HTTPException

app = FastAPI()

# Lista de contactos en memoria
contactos = [
    {
        #contacto 1
        "nombre": "fabricio",
        "apellido": "villagra",
        "edad": 19,
        "telefono": "3865647991",
        "email": "fabriciovilla88@gmail.com",
    },
    {
        #contaacto 2
        "nombre": "Ulises",
        "apellido": "Urquiza",
        "edad": 20,
        "telefono": "38652941",
        "email": "alejandraurquiza88@gmail.com",
    },
    {
        #contacto 3
        "nombre": "nacho",
        "apellido": "kermes",
        "edad": 20,
        "telefono": "3866528",
        "email": "nachokermes0188@gmail.com",
    },
    {
        #contacto 4
        "nombre": "lucas",
        "apellido": "umaño",
        "edad": 19,
        "telefono": "3868657991",
        "email": "lucasumaño55@gmail.com",
    },
    {
        #contacto 5
        "nombre": "lucas",
        "apellido": "albornoz",
        "edad": 19,
        "telefono": "38656473259",
        "email": "lucascool55988@gmail.com",
    },{
        #contacto 6
        "nombre": "martin",
        "apellido": "herrera",
        "edad": 19,
        "telefono": "3865644895",
        "email": "martin02388@gmail.com",
    },{
        #contacto 7
        "nombre": "luis",
        "apellido": "vera",
        "edad": 19,
        "telefono": "38659857",
        "email": "quridodiario@gmail.com",
    },{
        #contacto 8
        "nombre": "fabricio",
        "apellido": "bulovich",
        "edad": 19,
        "telefono": "3865647991",
        "email": "bulo888@gmail.com",
    },{
        #contacto 9
        "nombre": "ramiro",
        "apellido": "karake",
        "edad": 19,
        "telefono": "3865647991",
        "email": "carake555@gmail.com",
    },{
        #contacto 10
        "nombre": "juan",
        "apellido" :"pichon",
        "edad": 19,
        "telefono": "3865647991",
        "email": "lapichoneta9988@gmail.com",
    },
]

@app.get("/")
def bienvenida():
    return {"mensaje": "Servidor corriendo correctamente ✅"}

@app.get("/contactos")
def obtener_contactos():
    return contactos

# 📘 Buscar contacto por nombre (manejo de error si no existe)
@app.get("/contactos/{nombre}")
def obtener_contacto(nombre: str):
    for contacto in contactos:
        if contacto["nombre"].lower() == nombre.lower():
            return contacto
    # Si no se encuentra el contacto, lanzamos un error HTTP 404
    raise HTTPException(status_code=404, detail=f"El contacto '{nombre}' no fue encontrado.")

# 📗 Obtener contacto por índice (manejo de error de índice inválido)
@app.get("/contacto/indice/{indice}")
def obtener_contacto_por_indice(indice: int):
    if indice < 0 or indice >= len(contactos):
        raise HTTPException(
            status_code=400,
            detail=f"Índice inválido. Debe estar entre 0 y {len(contactos)-1}.",
        )
    return contactos[indice]
