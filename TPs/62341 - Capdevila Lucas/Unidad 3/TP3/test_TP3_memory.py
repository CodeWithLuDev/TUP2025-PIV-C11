import pytest
from fastapi.testclient import TestClient
import sqlite3
import os
import tempfile

# Cliente de prueba
client = TestClient(None)  # Se inicializará en el fixture

# ============== FIXTURES ==============

@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Se ejecuta antes y después de cada test usando base de datos en memoria"""
    # Crear una base de datos temporal
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    # Importar y configurar el módulo main
    import main
    original_db_name = main.DB_NAME
    main.DB_NAME = temp_db.name
    
    # Inicializar base de datos limpia
    main.init_db()
    
    # Configurar el cliente de prueba
    global client
    client = TestClient(main.app)
    
    yield
    
    # Restaurar la constante original
    main.DB_NAME = original_db_name
    
    # Limpiar archivo temporal
    try:
        os.unlink(temp_db.name)
    except:
        pass

# ============== TESTS DE MIGRACIÓN A SQLite ==============

def test_base_datos_se_crea():
    """Verifica que la base de datos se crea"""
    import main
    assert os.path.exists(main.DB_NAME), "La base de datos no existe"

def test_tabla_tareas_existe():
    """Verifica que la tabla 'tareas' existe con la estructura correcta"""
    import main
    conn = sqlite3.connect(main.DB_NAME)
    cursor = conn.cursor()
    
    # Verificar que la tabla existe
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='tareas'
    """)
    tabla = cursor.fetchone()
    assert tabla is not None, "La tabla 'tareas' no existe"
    
    # Verificar estructura de la tabla
    cursor.execute("PRAGMA table_info(tareas)")
    columnas = cursor.fetchall()
    
    nombres_columnas = [col[1] for col in columnas]
    assert "id" in nombres_columnas, "Falta la columna 'id'"
    assert "descripcion" in nombres_columnas, "Falta la columna 'descripcion'"
    assert "estado" in nombres_columnas, "Falta la columna 'estado'"
    assert "fecha_creacion" in nombres_columnas, "Falta la columna 'fecha_creacion'"
    assert "prioridad" in nombres_columnas, "Falta la columna 'prioridad'"
    
    # Verificar que id es PRIMARY KEY y AUTOINCREMENT
    columna_id = [col for col in columnas if col[1] == "id"][0]
    assert columna_id[5] == 1, "La columna 'id' debe ser PRIMARY KEY"
    
    # Verificar que descripcion y estado no aceptan NULL
    columna_descripcion = [col for col in columnas if col[1] == "descripcion"][0]
    columna_estado = [col for col in columnas if col[1] == "estado"][0]
    assert columna_descripcion[3] == 1, "La columna 'descripcion' debe ser NOT NULL"
    assert columna_estado[3] == 1, "La columna 'estado' debe ser NOT NULL"
    
    conn.close()

# ============== TESTS DE CRUD PERSISTENTE ==============

def test_crear_tarea():
    """POST /tareas - Crear una nueva tarea"""
    response = client.post("/tareas", json={
        "descripcion": "Tarea de prueba",
        "estado": "pendiente",
        "prioridad": "media"
    })
    
    assert response.status_code == 201, "Debe devolver status 201"
    data = response.json()
    assert data["id"] == 1, "El ID debe ser 1"
    assert data["descripcion"] == "Tarea de prueba"
    assert data["estado"] == "pendiente"
    assert data["prioridad"] == "media"
    assert "fecha_creacion" in data, "Debe incluir fecha_creacion"

def test_crear_tarea_descripcion_vacia():
    """POST /tareas - No debe permitir descripción vacía"""
    response = client.post("/tareas", json={
        "descripcion": "",
        "estado": "pendiente"
    })
    
    assert response.status_code == 422, "Debe rechazar descripción vacía"

def test_crear_tarea_estado_invalido():
    """POST /tareas - Solo debe aceptar estados válidos"""
    response = client.post("/tareas", json={
        "descripcion": "Tarea",
        "estado": "invalido"
    })
    
    assert response.status_code == 422, "Debe rechazar estados inválidos"

def test_obtener_todas_tareas():
    """GET /tareas - Obtener todas las tareas"""
    # Crear algunas tareas
    client.post("/tareas", json={"descripcion": "Tarea 1", "estado": "pendiente"})
    client.post("/tareas", json={"descripcion": "Tarea 2", "estado": "completada"})
    
    response = client.get("/tareas")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2, "Debe devolver 2 tareas"

def test_actualizar_tarea():
    """PUT /tareas/{id} - Actualizar una tarea"""
    # Crear tarea
    crear_response = client.post("/tareas", json={
        "descripcion": "Tarea original",
        "estado": "pendiente"
    })
    tarea_id = crear_response.json()["id"]
    
    # Actualizar tarea
    response = client.put(f"/tareas/{tarea_id}", json={
        "descripcion": "Tarea actualizada",
        "estado": "completada"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["descripcion"] == "Tarea actualizada"
    assert data["estado"] == "completada"

def test_eliminar_tarea():
    """DELETE /tareas/{id} - Eliminar una tarea"""
    # Crear tarea
    crear_response = client.post("/tareas", json={
        "descripcion": "Tarea a eliminar",
        "estado": "pendiente"
    })
    tarea_id = crear_response.json()["id"]
    
    # Eliminar tarea
    response = client.delete(f"/tareas/{tarea_id}")
    
    assert response.status_code == 200
    assert "mensaje" in response.json()
    
    # Verificar que fue eliminada
    get_response = client.get("/tareas")
    assert len(get_response.json()) == 0

# ============== TESTS DE BÚSQUEDAS Y FILTROS ==============

def test_filtro_por_estado():
    """GET /tareas?estado=... - Filtrar por estado"""
    # Crear tareas con diferentes estados
    client.post("/tareas", json={"descripcion": "Tarea 1", "estado": "pendiente"})
    client.post("/tareas", json={"descripcion": "Tarea 2", "estado": "completada"})
    client.post("/tareas", json={"descripcion": "Tarea 3", "estado": "pendiente"})
    
    # Filtrar por pendiente
    response = client.get("/tareas?estado=pendiente")
    tareas = response.json()
    
    assert len(tareas) == 2, "Debe devolver 2 tareas pendientes"
    assert all(t["estado"] == "pendiente" for t in tareas)

def test_filtro_por_prioridad():
    """GET /tareas?prioridad=... - Filtrar por prioridad"""
    # Crear tareas con diferentes prioridades
    client.post("/tareas", json={"descripcion": "Tarea 1", "prioridad": "alta"})
    client.post("/tareas", json={"descripcion": "Tarea 2", "prioridad": "baja"})
    client.post("/tareas", json={"descripcion": "Tarea 3", "prioridad": "alta"})
    
    # Filtrar por alta
    response = client.get("/tareas?prioridad=alta")
    tareas = response.json()
    
    assert len(tareas) == 2, "Debe devolver 2 tareas de prioridad alta"
    assert all(t["prioridad"] == "alta" for t in tareas)

# ============== TESTS DE MEJORAS OBLIGATORIAS ==============

def test_endpoint_resumen():
    """GET /tareas/resumen - Debe existir y devolver resumen"""
    # Crear tareas variadas
    client.post("/tareas", json={"descripcion": "T1", "estado": "pendiente", "prioridad": "alta"})
    client.post("/tareas", json={"descripcion": "T2", "estado": "pendiente", "prioridad": "baja"})
    client.post("/tareas", json={"descripcion": "T3", "estado": "completada", "prioridad": "alta"})
    
    response = client.get("/tareas/resumen")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verificar estructura
    assert "total_tareas" in data, "Debe incluir total_tareas"
    assert "por_estado" in data, "Debe incluir resumen por_estado"
    assert "por_prioridad" in data, "Debe incluir resumen por_prioridad"
    
    # Verificar conteos
    assert data["total_tareas"] == 3
    assert data["por_estado"]["pendiente"] == 2
    assert data["por_estado"]["completada"] == 1
    assert data["por_prioridad"]["alta"] == 2
    assert data["por_prioridad"]["baja"] == 1

def test_campo_prioridad_existe():
    """Verificar que el campo prioridad existe y funciona"""
    # Crear tarea con prioridad
    response = client.post("/tareas", json={
        "descripcion": "Tarea con prioridad",
        "estado": "pendiente",
        "prioridad": "alta"
    })
    
    assert response.status_code == 201
    data = response.json()
    assert "prioridad" in data, "Debe incluir campo prioridad"
    assert data["prioridad"] == "alta"

def test_completar_todas_tareas():
    """PUT /tareas/completar_todas - Marcar todas como completadas"""
    # Crear tareas con diferentes estados
    client.post("/tareas", json={"descripcion": "T1", "estado": "pendiente"})
    client.post("/tareas", json={"descripcion": "T2", "estado": "en_progreso"})
    
    # Completar todas
    response = client.put("/tareas/completar_todas")
    
    assert response.status_code == 200
    data = response.json()
    assert "mensaje" in data
    
    # Verificar que todas están completadas
    todas = client.get("/tareas").json()
    assert all(t["estado"] == "completada" for t in todas)

def test_endpoint_raiz():
    """GET / - Debe devolver información de la API"""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert "nombre" in data or "endpoints" in data, "Debe devolver info de la API"

# ============== RESUMEN DE EJECUCIÓN ==============

if __name__ == "__main__":
    print("=" * 70)
    print("TESTS DEL TP3 - API DE TAREAS PERSISTENTE (MEMORIA)")
    print("=" * 70)
    print("\nEjecutando tests...\n")
    
    # Ejecutar pytest con verbose
    pytest.main([__file__, "-v", "--tb=short"])
    
    print("\n" + "=" * 70)
    print("VERIFICACIÓN COMPLETA DE REQUISITOS DEL ENUNCIADO")
    print("=" * 70)
