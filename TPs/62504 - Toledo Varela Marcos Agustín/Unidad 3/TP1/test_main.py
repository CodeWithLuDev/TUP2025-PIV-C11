import requests

BASE_URL = "http://127.0.0.1:8000"

def test_raiz():
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    assert response.json() == {"mensaje": "Bienvenido a la Agenda de Contactos API"}

def test_listar_contactos():
    response = requests.get(f"{BASE_URL}/contactos")
    assert response.status_code == 200
    assert len(response.json()) == 10  # Debe haber 10 contactos cargados

def test_obtener_contacto_valido():
    response = requests.get(f"{BASE_URL}/contactos/0")
    assert response.status_code == 200
    assert response.json()["nombre"] == "Juan"  # El primero en la lista

def test_obtener_contacto_invalido():
    response = requests.get(f"{BASE_URL}/contactos/100")
    assert response.status_code == 404
    assert response.json()["detail"] == "Contacto no encontrado"