# TP4 – Relaciones entre Tablas y Filtros Avanzados

## 1. Descripción
Esta API permite gestionar **proyectos** y **tareas** relacionadas, utilizando **SQLite** como base de datos.

Incluye:
- CRUD de proyectos
- CRUD de tareas vinculadas a proyectos
- Relaciones 1:N entre tablas
- Eliminación en cascada (*ON DELETE CASCADE*)
- Filtros avanzados por estado, prioridad y orden
- Endpoints de estadísticas
- Validación con modelos Pydantic

---

## 2. Requisitos
- Python 3.10 o superior  
- Instalar dependencias:

```bash
pip install fastapi uvicorn
```
## 3. Archivos del Proyecto
- main.py / Contiene todos los endpoints de la API
- models.py / Modelos Pydantic para validar datos
- database.py /	Inicialización y manejo de la base de datos
- tareas.db	/ Base de datos SQLite con datos de prueba
- README.md / Documentación del proyecto

## 4. Cómo Iniciar el Servidor

1. Abrir la terminal dentro del proyecto
2. Ejecutar:
```bash
uvicorn main:app --reload
```
3. Abrir Swagger en el navegador:
```arduino
http://127.0.0.1:8000/docs
```
## 5. Estructura de la Base de Datos

### Tabla: proyectos
| Campo          | Tipo     | Restricciones               |
|----------------|----------|-----------------------------|
| id             | INTEGER  | PRIMARY KEY AUTOINCREMENT   |
| nombre         | TEXT     | NOT NULL, UNIQUE            |
| descripcion    | TEXT     | NULLABLE                    |
| fecha_creacion | TEXT     | NOT NULL                    |

### Tabla: tareas
| Campo          | Tipo     | Restricciones                                      |
|----------------|----------|----------------------------------------------------|
| id             | INTEGER  | PRIMARY KEY AUTOINCREMENT                          |
| descripcion    | TEXT     | NOT NULL                                          |
| estado         | TEXT     | NOT NULL (pendiente, en_progreso, completada)      |
| prioridad      | TEXT     | NOT NULL (baja, media, alta)                       |
| proyecto_id    | INTEGER  | FOREIGN KEY → proyectos(id) ON DELETE CASCADE     |
| fecha_creacion | TEXT     | NOT NULL                                          |

### Relación
- **1 Proyecto puede tener muchas Tareas (1:N)**  
- Si eliminás un **proyecto**, también se eliminan automáticamente **todas sus tareas**.

## 6. Ejemplos de Requests

### 📌 Crear un Proyecto
**POST /proyectos**
```json
{
  "nombre": "Proyecto Alpha",
  "descripcion": "Proyecto de prueba"
}
```

### Crear una tarea
**POST/tarea**
```json
{
  "descripcion": "Configurar entorno",
  "estado": "pendiente",
  "prioridad": "alta",
  "proyecto_id": 1
}
```
### Actualizar una Tarea
**PUT /tareas/1**
```json
{
  "descripcion": "Configurar entorno",
  "estado": "en_progreso",
  "prioridad": "alta",
  "proyecto_id": 1
}
```
## 7. Estadísticas Disponibles

La API incluye dos tipos de estadísticas:

---

### 📌 1. Estadísticas Generales  
**GET /estadisticas**

Devuelve:
- Total de proyectos
- Total de tareas
- Cantidad de tareas por estado:
  - pendientes
  - en progreso
  - completadas

---

### 📌 2. Estadísticas por Proyecto  
**GET /estadisticas/proyecto/{id}**

Incluye:
- Nombre del proyecto
- Total de tareas del proyecto
- Cantidad según estado:
  - pendientes
  - en progreso
  - completadas

---

## 8. Notas Finales

- Este TP implementa relaciones **1:N** usando claves foráneas en SQLite.  
- Se utilizaron filtros avanzados con parámetros opcionales en FastAPI.  
- Toda la API está documentada automáticamente en `/docs` gracias a **Swagger UI**.  
- La base de datos `tareas.db` se genera automáticamente al ejecutar el proyecto.

---














