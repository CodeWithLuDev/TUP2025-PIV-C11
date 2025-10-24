import sqlite3
from datetime import datetime, timedelta
import random

def crear_base_datos_con_datos():
    """Crea la base de datos tareas.db con datos de prueba"""
    
    # Conectar y habilitar foreign keys
    conn = sqlite3.connect('tareas.db')
    conn.execute('PRAGMA foreign_keys = ON')
    cursor = conn.cursor()
    
    # Eliminar tablas si existen (para empezar limpio)
    cursor.execute('DROP TABLE IF EXISTS tareas')
    cursor.execute('DROP TABLE IF EXISTS proyectos')
    
    # Crear tabla proyectos
    cursor.execute('''
        CREATE TABLE proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            descripcion TEXT,
            fecha_creacion TEXT NOT NULL
        )
    ''')
    
    # Crear tabla tareas con relación
    cursor.execute('''
        CREATE TABLE tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            prioridad TEXT NOT NULL,
            proyecto_id INTEGER NOT NULL,
            fecha_creacion TEXT NOT NULL,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
        )
    ''')
    
    print("✅ Tablas creadas correctamente")
    
    # Datos de prueba - Proyectos
    proyectos = [
        ("Proyecto Alpha", "Sistema de gestión empresarial", 
         (datetime.now() - timedelta(days=90)).isoformat()),
        ("Proyecto Beta", "Aplicación móvil de delivery", 
         (datetime.now() - timedelta(days=60)).isoformat()),
        ("Proyecto Gamma", "Plataforma de e-learning", 
         (datetime.now() - timedelta(days=30)).isoformat()),
        ("Proyecto Delta", "Dashboard de analytics", 
         (datetime.now() - timedelta(days=15)).isoformat()),
    ]
    
    cursor.executemany(
        'INSERT INTO proyectos (nombre, descripcion, fecha_creacion) VALUES (?, ?, ?)',
        proyectos
    )
    
    print(f"✅ {len(proyectos)} proyectos insertados")
    
    # Datos de prueba - Tareas
    tareas = [
        # Proyecto Alpha (ID: 1) - 8 tareas
        ("Diseñar base de datos", "completada", "alta", 1, 
         (datetime.now() - timedelta(days=85)).isoformat()),
        ("Implementar API REST", "completada", "alta", 1, 
         (datetime.now() - timedelta(days=80)).isoformat()),
        ("Crear frontend con React", "en_progreso", "alta", 1, 
         (datetime.now() - timedelta(days=70)).isoformat()),
        ("Configurar autenticación", "en_progreso", "media", 1, 
         (datetime.now() - timedelta(days=65)).isoformat()),
        ("Escribir tests unitarios", "pendiente", "media", 1, 
         (datetime.now() - timedelta(days=60)).isoformat()),
        ("Optimizar queries SQL", "pendiente", "baja", 1, 
         (datetime.now() - timedelta(days=55)).isoformat()),
        ("Documentar API", "pendiente", "media", 1, 
         (datetime.now() - timedelta(days=50)).isoformat()),
        ("Deploy en producción", "pendiente", "alta", 1, 
         (datetime.now() - timedelta(days=45)).isoformat()),
        
        # Proyecto Beta (ID: 2) - 10 tareas
        ("Investigar tecnologías móviles", "completada", "alta", 2, 
         (datetime.now() - timedelta(days=58)).isoformat()),
        ("Diseñar wireframes", "completada", "alta", 2, 
         (datetime.now() - timedelta(days=55)).isoformat()),
        ("Crear mockups en Figma", "completada", "media", 2, 
         (datetime.now() - timedelta(days=52)).isoformat()),
        ("Desarrollar splash screen", "completada", "baja", 2, 
         (datetime.now() - timedelta(days=48)).isoformat()),
        ("Implementar mapa interactivo", "en_progreso", "alta", 2, 
         (datetime.now() - timedelta(days=45)).isoformat()),
        ("Integrar pasarela de pago", "en_progreso", "alta", 2, 
         (datetime.now() - timedelta(days=40)).isoformat()),
        ("Sistema de notificaciones push", "en_progreso", "media", 2, 
         (datetime.now() - timedelta(days=35)).isoformat()),
        ("Chat en tiempo real", "pendiente", "alta", 2, 
         (datetime.now() - timedelta(days=30)).isoformat()),
        ("Sistema de calificaciones", "pendiente", "media", 2, 
         (datetime.now() - timedelta(days=25)).isoformat()),
        ("Testing en dispositivos", "pendiente", "alta", 2, 
         (datetime.now() - timedelta(days=20)).isoformat()),
        
        # Proyecto Gamma (ID: 3) - 6 tareas
        ("Análisis de requerimientos", "completada", "alta", 3, 
         (datetime.now() - timedelta(days=28)).isoformat()),
        ("Diseñar arquitectura del sistema", "completada", "alta", 3, 
         (datetime.now() - timedelta(days=25)).isoformat()),
        ("Crear módulo de cursos", "en_progreso", "alta", 3, 
         (datetime.now() - timedelta(days=20)).isoformat()),
        ("Implementar sistema de videos", "en_progreso", "alta", 3, 
         (datetime.now() - timedelta(days=18)).isoformat()),
        ("Panel de administración", "pendiente", "media", 3, 
         (datetime.now() - timedelta(days=15)).isoformat()),
        ("Sistema de certificados", "pendiente", "baja", 3, 
         (datetime.now() - timedelta(days=12)).isoformat()),
        
        # Proyecto Delta (ID: 4) - 5 tareas
        ("Conectar con fuentes de datos", "completada", "alta", 4, 
         (datetime.now() - timedelta(days=14)).isoformat()),
        ("Crear gráficos con Chart.js", "en_progreso", "alta", 4, 
         (datetime.now() - timedelta(days=10)).isoformat()),
        ("Implementar filtros avanzados", "en_progreso", "media", 4, 
         (datetime.now() - timedelta(days=8)).isoformat()),
        ("Exportar reportes PDF", "pendiente", "media", 4, 
         (datetime.now() - timedelta(days=5)).isoformat()),
        ("Optimizar rendimiento", "pendiente", "baja", 4, 
         (datetime.now() - timedelta(days=3)).isoformat()),
    ]
    
    cursor.executemany(
        'INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion) VALUES (?, ?, ?, ?, ?)',
        tareas
    )
    
    print(f"✅ {len(tareas)} tareas insertadas")
    
    # Commit y cerrar
    conn.commit()
    conn.close()
    
    print("\n" + "="*60)
    print("🎉 Base de datos 'tareas.db' creada exitosamente!")
    print("="*60)
    print("\n📊 Resumen de datos:")
    print(f"   • {len(proyectos)} proyectos")
    print(f"   • {len(tareas)} tareas")
    print("\n📋 Distribución por proyecto:")
    print("   • Proyecto Alpha: 8 tareas")
    print("   • Proyecto Beta: 10 tareas")
    print("   • Proyecto Gamma: 6 tareas")
    print("   • Proyecto Delta: 5 tareas")
    print("\n✅ Listo para usar con la API")
    print("="*60 + "\n")

if __name__ == "__main__":
    crear_base_datos_con_datos()