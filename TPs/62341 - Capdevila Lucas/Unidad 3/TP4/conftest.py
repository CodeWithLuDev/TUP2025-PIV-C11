import pytest
import os
import time
import sqlite3
from fastapi.testclient import TestClient
from main import app
from database import DB_NAME, close_all_connections


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """
    Antes de todos los tests, elimina la BD anterior si existe y crea una nueva.
    Después de todos los tests, la elimina de forma segura.
    """
    # Eliminar base vieja si quedó bloqueada
    if os.path.exists(DB_NAME):
        for _ in range(10):
            try:
                os.remove(DB_NAME)
                break
            except PermissionError:
                time.sleep(0.1)

    yield  # ← Aquí se ejecutan los tests

    # Limpiar conexiones y eliminar al final
    close_all_connections()
    for _ in range(10):
        try:
            os.remove(DB_NAME)
            break
        except PermissionError:
            time.sleep(0.1)


@pytest.fixture(scope="session")
def test_client():
    """
    Crea un cliente de prueba de FastAPI reutilizable para toda la sesión.
    """
    # Crear y cerrar cliente una vez por session pero usando context manager
    from fastapi.testclient import TestClient
    from main import app

    with TestClient(app) as client:
        yield client


@pytest.fixture(autouse=True, scope="function")
def clean_after_test():
    """
    Limpia cualquier conexión pendiente entre tests (Windows-friendly).
    """
    yield
    # Cerrar una conexión directa para evitar locks en Windows
    try:
        sqlite3.connect(DB_NAME).close()
    except Exception:
        pass
    close_all_connections()
    time.sleep(0.05)
