### Ejercicio N°3: Validacion del Echo Server

**Solución:** Se crea un script de bash que utiliza netcat dentro de un contenedor para validar el funcionamiento del servidor echo, enviando un mensaje de prueba y verificando que el servidor responda con el mismo mensaje, todo sin exponer puertos del servidor ni instalar netcat en el host.

#### Cómo ejecutar:
```bash
# Ejecutar validación del echo server
./validar-echo-server.sh

# O ejecutando
make docker-compose-up
```

#### Solución implementada:

**Archivo principal:**
- `validar-echo-server.sh`: Script de validación que utiliza netcat en contenedor


**Validación automática**: Compara mensaje enviado vs respuesta recibida



