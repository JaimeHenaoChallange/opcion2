#!/bin/bash

# Salir inmediatamente si un comando falla
set -e

# Mostrar un mensaje de inicio
echo "🔧 Configurando el entorno y ejecutando el script monitor.py..."

# Verificar que el archivo monitor.py existe
if [ ! -f /app/monitor.py ]; then
  echo "❌ El archivo monitor.py no se encuentra en /app. Abortando."
  exit 1
fi

# Mostrar el contenido del directorio actual para depuración
echo "📂 Contenido del directorio /app:"
ls -l /app

# Ejecutar el script en modo sin búfer
exec python -u /app/monitor.py
