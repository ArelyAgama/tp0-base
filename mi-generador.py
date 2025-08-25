#!/usr/bin/env python3

import sys

def generar_docker_compose(archivo_salida, cantidad_clientes):
    """
    Genera un archivo docker-compose.yaml con la cantidad especificada de clientes
    """
    
    # Contenido base del docker-compose
    contenido = f"""name: tp0
services:
  server:
    container_name: server
    image: server:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
      - LOGGING_LEVEL=DEBUG
    volumes:
      - ./server/config.ini:/config.ini
    networks:
      - testing_net
"""
    
    # Agregar clientes dinámicamente
    for i in range(1, cantidad_clientes + 1):
        contenido += f"""
  client{i}:
    container_name: client{i}
    image: client:latest
    entrypoint: /client
    environment:
      - CLI_ID={i}
      - CLI_LOG_LEVEL=DEBUG
    volumes:
      - ./client/config.yaml:/config.yaml
    networks:
      - testing_net
    depends_on:
      - server
"""
    
    # Agregar la red al final
    contenido += """
networks:
  testing_net:
    ipam:
      driver: default
      config:
        - subnet: 172.25.125.0/24
"""
    
    # Escribir el archivo
    try:
        with open(archivo_salida, 'w') as file:
            file.write(contenido)
        
        print(f"📝 Archivo {archivo_salida} generado con:")
        print(f"   • 1 servidor")
        print(f"   • {cantidad_clientes} clientes (client1 a client{cantidad_clientes})")
        print(f"   • Red: testing_net (172.25.125.0/24)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al escribir el archivo: {e}")
        return False

def main():
    if len(sys.argv) != 3:
        print("Uso: python3 mi-generador.py <archivo_salida> <cantidad_clientes>")
        sys.exit(1)
    
    archivo_salida = sys.argv[1]
    try:
        cantidad_clientes = int(sys.argv[2])
    except ValueError:
        print("❌ Error: La cantidad de clientes debe ser un número")
        sys.exit(1)
    
    if cantidad_clientes <= 0:
        print("❌ Error: La cantidad de clientes debe ser mayor a 0")
        sys.exit(1)
    
    if cantidad_clientes > 100:
        print("⚠️  Advertencia: Generar más de 100 clientes puede ser intensivo")
        respuesta = input("¿Continuar? (y/N): ")
        if respuesta.lower() != 'y':
            print("Operación cancelada")
            sys.exit(0)
    
    success = generar_docker_compose(archivo_salida, cantidad_clientes)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
