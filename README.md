### Ejercicio N°1: Generador de Docker Compose

**Objetivo:** Definir un script de bash `generar-compose.sh` que permita crear una definición de Docker Compose con una cantidad configurable de clientes.

#### Como ejecutar:
```bash
# Generar un docker-compose con 5 clientes
./generar-compose.sh docker-compose-dev.yaml 5

# Generar un docker-compose con 3 clientes
./generar-compose.sh mi-compose.yaml 3
```

#### Solución implementada:

**Archivos principales:**
- `generar-compose.sh`: Script bash principal que valida parámetros y llama al generador Python
- `mi-generador.py`: Generador Python que crea el archivo Docker Compose dinámicamente

**Características de la solución:**
- **Validación de parámetros**: El script bash verifica que se pasen exactamente 2 parámetros
- **Nomenclatura consistente**: Los containers siguen el formato `client1`, `client2`, `client3`, etc.
- **Configuración dinámica**: Permite generar cualquier cantidad de clientes (1 a N)
- **Red personalizada**: Utiliza la red `testing_net` con subnet `172.25.125.0/24`
- **Dependencias**: Cada cliente depende del servidor para su inicio
- **Variables de entorno**: Cada cliente recibe su ID único (`CLI_ID={i}`)
