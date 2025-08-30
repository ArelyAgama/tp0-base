import sys

def generar_docker_compose(archivo_salida, cantidad_clientes):
    
    contenido = f"""name: tp0
services:
  server:
    container_name: server
    image: server:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
      - LOGGING_LEVEL=DEBUG
    networks:
      - testing_net
"""
    
    # Agregar clientes 
    for i in range(1, cantidad_clientes + 1):
        contenido += f"""
  client{i}:
    container_name: client{i}
    image: client:latest
    entrypoint: /client
    environment:
      - CLI_ID={i}
      - CLI_LOG_LEVEL=DEBUG
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
    
    # Escribo el archivo de salida
    try:
        with open(archivo_salida, 'w') as file:
            file.write(contenido)
        
        print(f"Archivo {archivo_salida} generado con:")
        print(f"   - 1 servidor")
        if cantidad_clientes > 0:
            print(f"   - {cantidad_clientes} clientes (client1 a client{cantidad_clientes})")
        else:
            print(f"   - 0 clientes")
        print(f"   - Red: testing_net (172.25.125.0/24)")
        
        return True
        
    except Exception as e:
        print(f"Error al escribir el archivo: {e}")
        return False

def main():
    archivo_salida = sys.argv[1]
    cantidad_clientes = int(sys.argv[2])
    
    success = generar_docker_compose(archivo_salida, cantidad_clientes)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
