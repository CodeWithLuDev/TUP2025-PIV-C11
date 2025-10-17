import pytest
from fastapi.testclient import TestClient
from main import app, init_db, DB_NAME
import sqlite3
import os

# Cliente de prueba
client = TestClient(app)

# ============== FIXTURES ==============

@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Se ejecuta antes y después de cada test"""
    # Antes del test: eliminar base de datos si existe
    if os.path.exists(DB_NAME):
        try:
            os.remove(DB_NAME)
        except PermissionError:
            # Si no se puede eliminar, continuar
            pass
    
    # Inicializar base de datos limpia
    init_db()
    
    yield
    
    # Después del test: limpiar de manera segura
    if os.path.exists(DB_NAME):
        try:
            # Cerrar todas las conexiones primero
            import gc
            gc.collect()
            os.remove(DB_NAME)
        except PermissionError:
            # Si no se puede eliminar, no es crítico
            pass

# ============== TESTS DE MIGRACIÓN A SQLite ==============

def test_base_datos_se_crea():
    """Verifica que la base de datos tareas.db se crea"""
    assert os.path.exists(DB_NAME), "La base de datos tareas.db no existe"

def test_tabla_tareas_existe():
    """Verifica que la tabla 'tareas' existe con la estructura correcta"""
    conn = sqlite3.connect(DB_NAME)
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

def test_crear_tarea_descripcion_solo_espacios():
    """POST /tareas - No debe permitir descripción con solo espacios"""
    response = client.post("/tareas", json={
        "descripcion": "   ",
        "estado": "pendiente"
    })
    
    assert response.status_code == 422, "Debe rechazar descripción con solo espacios"

def test_crear_tarea_estado_invalido():
    """POST /tareas - Solo debe aceptar estados válidos"""
    response = client.post("/tareas", json={
        "descripcion": "Tarea",
        "estado": "invalido"
    })
    
    assert response.status_code == 422, "Debe rechazar estados inválidos"

def test_crear_tarea_estados_validos():
    """POST /tareas - Debe aceptar los tres estados válidos"""
    estados_validos = ["pendiente", "en_progreso", "completada"]
    
    for estado in estados_validos:
        response = client.post("/tareas", json={
            "descripcion": f"Tarea {estado}",
            "estado": estado
        })
        assert response.status_code == 201, f"Debe aceptar el estado '{estado}'"
        assert response.json()["estado"] == estado

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

def test_actualizar_tarea_inexistente():
    """PUT /tareas/{id} - Debe devolver 404 para tarea inexistente"""
    response = client.put("/tareas/999", json={
        "descripcion": "No existe",
        "estado": "pendiente"
    })
    
    assert response.status_code == 404, "Debe devolver 404 para tarea inexistente"
    assert "error" in response.json()["detail"]

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

def test_eliminar_tarea_inexistente():
    """DELETE /tareas/{id} - Debe devolver 404 para tarea inexistente"""
    response = client.delete("/tareas/999")
    
    assert response.status_code == 404, "Debe devolver 404 para tarea inexistente"

# ============== TESTS DE PERSISTENCIA ==============

def test_persistencia_datos():
    """Verifica que los datos persisten en la base de datos"""
    # Crear una tarea
    client.post("/tareas", json={
        "descripcion": "Tarea persistente",
        "estado": "pendiente",
        "prioridad": "alta"
    })
    
    # Verificar directamente en la base de datos
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tareas WHERE descripcion = 'Tarea persistente'")
    tarea = cursor.fetchone()
    conn.close()
    
    assert tarea is not None, "La tarea debe estar en la base de datos"
    assert tarea[1] == "Tarea persistente", "La descripción debe coincidir"
    assert tarea[2] == "pendiente", "El estado debe coincidir"

def test_datos_persisten_tras_reinicio():
    """Simula reinicio: los datos deben seguir en la DB"""
    # Crear tarea
    client.post("/tareas", json={
        "descripcion": "Tarea antes de reinicio",
        "estado": "pendiente"
    })
    
    # Simular "reinicio": crear nuevo cliente (la DB sigue existiendo)
    nuevo_client = TestClient(app)
    
    # Verificar que la tarea sigue ahí
    response = nuevo_client.get("/tareas")
    tareas = response.json()
    
    assert len(tareas) >= 1, "Las tareas deben persistir"
    assert any(t["descripcion"] == "Tarea antes de reinicio" for t in tareas)

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

def test_filtro_por_texto():
    """GET /tareas?texto=... - Filtrar por texto en descripción"""
    # Crear tareas
    client.post("/tareas", json={"descripcion": "Comprar pan", "estado": "pendiente"})
    client.post("/tareas", json={"descripcion": "Estudiar Python", "estado": "pendiente"})
    client.post("/tareas", json={"descripcion": "Comprar leche", "estado": "pendiente"})
    
    # Buscar "comprar"
    response = client.get("/tareas?texto=comprar")
    tareas = response.json()
    
    assert len(tareas) == 2, "Debe encontrar 2 tareas con 'comprar'"
    assert all("comprar" in t["descripcion"].lower() for t in tareas)

def test_filtro_por_prioridad():
    """GET /tareas?prioridad=... - Filtrar por prioridad (mejora obligatoria)"""
    # Crear tareas con diferentes prioridades
    client.post("/tareas", json={"descripcion": "Tarea 1", "prioridad": "alta"})
    client.post("/tareas", json={"descripcion": "Tarea 2", "prioridad": "baja"})
    client.post("/tareas", json={"descripcion": "Tarea 3", "prioridad": "alta"})
    
    # Filtrar por alta
    response = client.get("/tareas?prioridad=alta")
    tareas = response.json()
    
    assert len(tareas) == 2, "Debe devolver 2 tareas de prioridad alta"
    assert all(t["prioridad"] == "alta" for t in tareas)

def test_ordenamiento_descendente():
    """GET /tareas?orden=desc - Ordenar por fecha descendente"""
    # Crear tareas en secuencia
    import time
    client.post("/tareas", json={"descripcion": "Primera"})
    time.sleep(0.1)
    client.post("/tareas", json={"descripcion": "Segunda"})
    time.sleep(0.1)
    client.post("/tareas", json={"descripcion": "Tercera"})
    
    # Obtener tareas ordenadas descendente (más reciente primero)
    response = client.get("/tareas?orden=desc")
    tareas = response.json()
    
    assert tareas[0]["descripcion"] == "Tercera", "La más reciente debe ser primera"
    assert tareas[-1]["descripcion"] == "Primera", "La más antigua debe ser última"

def test_ordenamiento_ascendente():
    """GET /tareas?orden=asc - Ordenar por fecha ascendente"""
    # Crear tareas en secuencia
    import time
    client.post("/tareas", json={"descripcion": "Primera"})
    time.sleep(0.1)
    client.post("/tareas", json={"descripcion": "Segunda"})
    time.sleep(0.1)
    client.post("/tareas", json={"descripcion": "Tercera"})
    
    # Obtener tareas ordenadas ascendente (más antigua primero)
    response = client.get("/tareas?orden=asc")
    tareas = response.json()
    
    assert tareas[0]["descripcion"] == "Primera", "La más antigua debe ser primera"
    assert tareas[-1]["descripcion"] == "Tercera", "La más reciente debe ser última"

def test_filtros_combinados():
    """GET /tareas - Combinar múltiples filtros"""
    # Crear tareas variadas
    client.post("/tareas", json={
        "descripcion": "Comprar pan urgente",
        "estado": "pendiente",
        "prioridad": "alta"
    })
    client.post("/tareas", json={
        "descripcion": "Comprar leche",
        "estado": "completada",
        "prioridad": "baja"
    })
    client.post("/tareas", json={
        "descripcion": "Estudiar",
        "estado": "pendiente",
        "prioridad": "alta"
    })
    
    # Filtrar: pendiente + prioridad alta + texto "comprar"
    response = client.get("/tareas?estado=pendiente&prioridad=alta&texto=comprar")
    tareas = response.json()
    
    assert len(tareas) == 1, "Solo debe haber 1 tarea con todos los filtros"
    assert tareas[0]["descripcion"] == "Comprar pan urgente"

# ============== TESTS DE MEJORAS OBLIGATORIAS ==============

def test_endpoint_resumen():
    """GET /tareas/resumen - Debe existir y devolver resumen"""
    # Crear tareas variadas
    client.post("/tareas", json={"descripcion": "T1", "estado": "pendiente", "prioridad": "alta"})
    client.post("/tareas", json={"descripcion": "T2", "estado": "pendiente", "prioridad": "baja"})
    client.post("/tareas", json={"descripcion": "T3", "estado": "completada", "prioridad": "alta"})
    client.post("/tareas", json={"descripcion": "T4", "estado": "en_progreso", "prioridad": "media"})
    
    response = client.get("/tareas/resumen")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verificar estructura
    assert "total_tareas" in data, "Debe incluir total_tareas"
    assert "por_estado" in data, "Debe incluir resumen por_estado"
    assert "por_prioridad" in data, "Debe incluir resumen por_prioridad"
    
    # Verificar conteos
    assert data["total_tareas"] == 4
    assert data["por_estado"]["pendiente"] == 2
    assert data["por_estado"]["completada"] == 1
    assert data["por_estado"]["en_progreso"] == 1
    assert data["por_prioridad"]["alta"] == 2
    assert data["por_prioridad"]["baja"] == 1
    assert data["por_prioridad"]["media"] == 1

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

def test_prioridades_validas():
    """Solo debe aceptar prioridades válidas: baja, media, alta"""
    prioridades_validas = ["baja", "media", "alta"]
    
    for prioridad in prioridades_validas:
        response = client.post("/tareas", json={
            "descripcion": f"Tarea {prioridad}",
            "prioridad": prioridad
        })
        assert response.status_code == 201, f"Debe aceptar prioridad '{prioridad}'"

def test_prioridad_invalida():
    """No debe aceptar prioridades inválidas"""
    response = client.post("/tareas", json={
        "descripcion": "Tarea",
        "prioridad": "urgente"  # No es válida
    })
    
    assert response.status_code == 422, "Debe rechazar prioridades inválidas"

def test_validacion_con_pydantic():
    """Verificar que se usa Pydantic para validación"""
    # Intentar crear tarea sin descripción (campo requerido)
    response = client.post("/tareas", json={
        "estado": "pendiente"
    })
    
    assert response.status_code == 422, "Pydantic debe validar campos requeridos"

def test_completar_todas_tareas():
    """PUT /tareas/completar_todas - Marcar todas como completadas"""
    # Crear tareas con diferentes estados
    client.post("/tareas", json={"descripcion": "T1", "estado": "pendiente"})
    client.post("/tareas", json={"descripcion": "T2", "estado": "en_progreso"})
    client.post("/tareas", json={"descripcion": "T3", "estado": "completada"})
    
    # Completar todas
    response = client.put("/tareas/completar_todas")
    
    assert response.status_code == 200
    data = response.json()
    assert "mensaje" in data
    
    # Verificar que todas están completadas
    todas = client.get("/tareas").json()
    assert all(t["estado"] == "completada" for t in todas)

# ============== TEST DE ENDPOINT RAÍZ ==============

def test_endpoint_raiz():
    """GET / - Debe devolver información de la API"""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert "nombre" in data or "endpoints" in data, "Debe devolver info de la API"

# ============== RESUMEN DE EJECUCIÓN ==============

if __name__ == "__main__":
    print("=" * 70)
    print("TESTS DEL TP3 - API DE TAREAS PERSISTENTE")
    print("=" * 70)
    print("\nEjecutando tests...\n")
    
    # Ejecutar pytest con verbose
    pytest.main([__file__, "-v", "--tb=short"])
    
    print("\n" + "=" * 70)
    print("VERIFICACIÓN COMPLETA DE REQUISITOS DEL ENUNCIADO")
    print("=" * 70)