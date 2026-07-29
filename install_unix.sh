#!/bin/bash
set -e

echo "🔧 Configurando entorno virtual..."
if [ ! -d "venv" ]; then
    echo "Creando nuevo entorno virtual..."
    python3 -m venv venv
fi

# Verificar que el venv funciona
if [ ! -f "./venv/bin/pip" ]; then
    echo "❌ Error: El entorno virtual no se creó correctamente."
    echo "Intentá:"
    echo "  1. Eliminarlo manualmente: rm -rf venv"
    echo "  2. Instalar python3-venv si es necesario: sudo apt-get install python3-venv"
    echo "  3. Volver a ejecutar este script"
    exit 1
fi

echo "📦 Actualizando pip..."
./venv/bin/pip install --upgrade pip

echo "📚 Instalando dependencias del proyecto..."
./venv/bin/pip install -e .

echo "🌐 Instalando Chromium para Playwright..."
./venv/bin/playwright install chromium

echo "✅ Instalación completada!"
echo "Para activar el entorno virtual, ejecutá: source venv/bin/activate"
