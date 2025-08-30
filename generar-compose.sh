# Verificar que se enviaron 2 parametros
if [ $# -ne 2 ]; then
    echo "Ingresar: $0 <archivo_salida> <cantidad_clientes>"
    echo "Ejemplo: $0 docker-compose-dev.yaml 5"
    exit 1
fi

# Parametros
ARCHIVO_SALIDA=$1
CANTIDAD_CLIENTES=$2

echo "Nombre del archivo de salida: $ARCHIVO_SALIDA"
echo "Cantidad de clientes: $CANTIDAD_CLIENTES"

# Llamo a mi generador que crea el docker compose
python3 mi-generador.py "$ARCHIVO_SALIDA" "$CANTIDAD_CLIENTES"