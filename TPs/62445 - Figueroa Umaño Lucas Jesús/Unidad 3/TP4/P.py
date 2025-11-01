import sqlite3 

def init_db():
    """Inicializa las tablas de la base de datos"""
    conn = sqlite3.connect('Proyectos.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS proyectos 
                   (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   nombre TEXT NOT NULL UNIQUE,
                   descripcion TEXT,
                   fecha_creacion TEXT NOT NULL
                   )
            ''')

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tareas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descripcion TEXT NOT NULL,
        estado TEXT NOT NULL CHECK(estado IN ('pendiente', 'en_progreso', 'completada')) DEFAULT 'pendiente',
        prioridad TEXT NOT NULL CHECK(prioridad IN ('baja', 'media', 'alta')) DEFAULT 'media',
        fecha_creacion TEXT DEFAULT (datetime('now', 'localtime')),
        proyecto_id INTEGER NOT NULL,
        FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
    )
    """)

    conn.commit()
    conn.close()
    print("✓ Base de datos inicializada exitosamente")


def insertar_proyecto(nombre, descripcion, fecha_creacion):
    """Inserta un proyecto y sus tareas asociadas"""
    conn = sqlite3.connect('Proyectos.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO proyectos (nombre, descripcion, fecha_creacion)
        VALUES (?, ?, ?)
    ''', (nombre, descripcion, fecha_creacion))
    
    proyecto_id = cursor.lastrowid
    
    
    tareas = [
        ("Planificar el desarrollo", "en_progreso", "alta", proyecto_id),
        ("Presentacion de diseños", "pendiente", "alta", proyecto_id),
        ("Eleccion de materiales", "pendiente", "media", proyecto_id),
        ("Ramificacion de versiones", "pendiente", "baja", proyecto_id)
    ]
    
    cursor.executemany("""
        INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id)
        VALUES (?, ?, ?, ?)
    """, tareas)

    conn.commit()
    conn.close()
    
    print(f"✓ Proyecto '{nombre}' y tareas insertados exitosamente con ID: {proyecto_id}")
    return proyecto_id



if __name__ == "__main__":
 
    init_db()
    
    insertar_proyecto(
        'Proyecto Terminator', 
        'Desarrollo de muñeco del T800', 
        '15/10/2025'
    )

    insertar_proyecto(
        'Proyecto Apolo 11', 
        'Jueguetes a escala 1/68', 
        '20/10/2025'
    )