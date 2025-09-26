import requests

def test_raiz():
    response = requests.get("http://127.0.0.1:8000/")
    assert response.status_code == 200
    assert response.json() == {"mensaje": "Bienvenido a la Agenda de Contactos API"}

def test_contactos():
    response = requests.get("http://127.0.0.1:8000/contactos")
    assert response.status_code == 200
    assert len(response.json()) == 10  # Verifica que haya 10 contactos