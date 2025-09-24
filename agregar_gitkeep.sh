#!/bin/bash

# Verifica que exista la carpeta TPs
if [ ! -d "TPs" ]; then
  echo "❌ No se encontró la carpeta TPs. Asegúrate de estar en la raíz del repositorio."
  exit 1
fi

echo "🔍 Buscando carpetas vacías dentro de TPs..."

# Encuentra todas las carpetas vacías dentro de TPs y agrega un .gitkeep
find TPs -type d -empty -exec sh -c 'echo "➕ Agregando .gitkeep en $1"; touch "$1/.gitkeep"' _ {} \;

echo "✅ Listo: se agregaron archivos .gitkeep en todas las carpetas vacías."
echo "ℹ️ Ahora ejecuta:"
echo "   git add ."
echo "   git commit -m \"Agrego .gitkeep para mantener la estructura de carpetas\""
echo "   git push"
