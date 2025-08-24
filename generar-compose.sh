#!/bin/bash

# Verificar que se pasaron los parámetros correctos
if [ $# -ne 2 ]; then
    echo "Uso: $0 <archivo_salida> <cantidad_clientes>"
    echo "Ejemplo: $0 docker-compose-dev.yaml 5"
    exit 1
fi

# Obtener parámetros
ARCHIVO_SALIDA=$1
CANTIDAD_CLIENTES=$2

echo "Nombre del archivo de salida: $ARCHIVO_SALIDA"
echo "Cantidad de clientes: $CANTIDAD_CLIENTES"

# Validar que la cantidad de clientes sea un número positivo
if ! [[ "$CANTIDAD_CLIENTES" =~ ^[0-9]+$ ]] || [ "$CANTIDAD_CLIENTES" -eq 0 ]; then
    echo "Error: La cantidad de clientes debe ser un número positivo"
    exit 1
fi

# Llamar al script de Python para generar el docker-compose
python3 mi-generador.py "$ARCHIVO_SALIDA" "$CANTIDAD_CLIENTES"

if [ $? -eq 0 ]; then
    echo "✅ Archivo $ARCHIVO_SALIDA generado exitosamente con $CANTIDAD_CLIENTES clientes"
else
    echo "❌ Error al generar el archivo $ARCHIVO_SALIDA"
    exit 1
fi
