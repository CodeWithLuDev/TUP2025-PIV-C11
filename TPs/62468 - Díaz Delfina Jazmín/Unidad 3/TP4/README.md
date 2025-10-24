TP4/
├── main.py          ← Código principal de la API
├── models.py        ← Modelos de validación
├── database.py      ← Funciones de base de datos
├── README.md        ← Manual de usuario
└── tareas.db        ← Se crea automáticamente al iniciar
```

---

##  IMPORTANTE: Consejos para evitar errores

### **1. Usa un editor de código adecuado**

**NO uses:** Microsoft Word
 **SÍ usa:** 
- Visual Studio Code (recomendado) - [Descargar gratis](https://code.visualstudio.com/)
- Notepad++ (Windows)
- Sublime Text
- PyCharm
- Bloc de notas (funciona, pero no es ideal)

---

### **2. Verifica la extensión del archivo**

En Windows, a veces los archivos se guardan como `main.py.txt` en vez de `main.py`

**Solución:**
1. Abre el Explorador de archivos
2. Ve a la pestaña "Vista"
3. Activa "Extensiones de nombre de archivo"
4. Verifica que los archivos terminen en `.py` y NO en `.py.txt`

---

### **3. Todos los archivos en la MISMA carpeta**

Los 3 archivos Python **DEBEN** estar juntos:
```
 CORRECTO:
TP4/
├── main.py
├── models.py
└── database.py

 INCORRECTO:
TP4/
├── codigo/
│   └── main.py
├── models.py
└── database.py