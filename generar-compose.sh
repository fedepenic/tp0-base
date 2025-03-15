#!/bin/bash

# Verifica que se pasen dos argumentos
if [ "$#" -ne 2 ]; then
    echo "Uso: $0 <archivo_salida> <cantidad_clientes>"
    exit 1
fi

ARCHIVO_SALIDA=$1
CANTIDAD_CLIENTES=$2

echo "Generando archivo Docker Compose: $ARCHIVO_SALIDA con $CANTIDAD_CLIENTES clientes..."

# Llama al script de Python para generar el archivo
python3 mi-generador.py "$ARCHIVO_SALIDA" "$CANTIDAD_CLIENTES"

echo "Archivo generado exitosamente: $ARCHIVO_SALIDA"
