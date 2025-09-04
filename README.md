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



### Ejercicio N°4: Manejo Graceful de SIGTERM

**Solución:** Se implementa el manejo de la señal SIGTERM tanto en el cliente como en el servidor para permitir un cierre graceful de las aplicaciones, cerrando correctamente todos los recursos (sockets, conexiones) y loggeando cada paso del proceso de shutdown, usando un channel para recibir SIGTERM del lado del cliente y un handler de signals del lado del servidor.

#### Cómo ejecutar:
```bash
make docker-compose-up

```

### Ejercicio N°5: Sistema de Lotería Nacional

**Solución:** Se implementa un sistema de lotería nacional donde las agencias envían apuestas al servidor central, utilizando un protocolo de comunicación personalizado con manejo de short read/write y separación clara entre capa de comunicación y modelo de dominio.

#### Cómo ejecutar:
```bash

make docker-compose-up


```

#### Solución implementada:

**Estructura del sistema:**
- **Cliente (Agencia)**: Envía apuestas con datos de persona (nombre, apellido, DNI, nacimiento, número)
- **Servidor (Central)**: Recibe y almacena apuestas usando la función `store_bet()` provista
- **Protocolo de comunicación**: Header de 4 bytes + mensaje serializado
- **Separación de responsabilidades**: Módulos `protocol.go/py` para comunicación, `utils.py` para dominio

**Protocolo de comunicación:**
- **Formato de mensaje**: `AGENCIA/NOMBRE/APELLIDO/DOCUMENTO/NACIMIENTO/NUMERO`
- **Header**: 4 bytes con longitud del mensaje (ej: "0051" para mensaje de 51 bytes)
- **Serialización**: Separación por "/" en cliente, parsing en servidor
- **ACK**: Servidor responde con `ACK/DNI/NUMERO` para confirmar recepción

**Manejo de short read/write:**
- **Cliente (Go)**: Funciones `handleShortRead()` y `handleShortWrite()` en `protocol.go`
- **Servidor (Python)**: Funciones `_handle_short_read()` y `_handle_short_write()` en `protocol.py`
- **Garantías**: Se asegura lectura/escritura completa de mensajes independientemente del tamaño

**Modelo de dominio:**
- **Cliente**: Struct `Bet` con campos de la apuesta
- **Servidor**: Clase `Bet` en `utils.py` con validaciones y conversiones de tipos
- **Persistencia**: Almacenamiento en CSV usando `store_bets()` de la cátedra

### Ejercicio N°6: Procesamiento por Batches

**Solución:** Se implementa el procesamiento por batches de apuestas, donde los clientes leen archivos CSV y envían múltiples apuestas por batches optimizando la transmisión y procesamiento. El servidor valida cada batch completo y responde con códigos de éxito o error. Ademas para este ejercico se realiza un analisis previo de los csv otorgados por la catedra.

#### Cómo ejecutar:
```bash

make docker-compose-up

```

#### Solución implementada:

**Cálculo del tamaño máximo por batch:**
- **Análisis de archivos CSV**: Se analizaron los archivos `agency-1.csv` a `agency-5.csv` proporcionados por la cátedra
- **Datos reales encontrados**:
  - El nombre más largo tiene 23 caracteres
  - El apellido más largo tiene 10 caracteres  
  - El DNI más largo es 8 caracteres
  - La fecha más larga tiene 10 caracteres
  - El número más largo tiene 4 caracteres
- **Apuesta más larga encontrada**: `1/Milagros De Los Angeles/Valenzuela/25748564/1984-05-22/5142` (61 caracteres)
- **Límite de 8KB**: Con header de 4 bytes + mensaje, el límite efectivo es 8188 bytes
- **Cálculo real**: `8188 / 61 = 134` apuestas máximo por batch
- **Configuración final**: Se estableció `batch.maxAmount: 99` para mantener margen de seguridad

**Protocolo de comunicación por batch:**
- **Header de 4 bytes**: Contiene el tamaño total del mensaje (`"0051"` para 51 bytes)
- **Primera línea del mensaje**: `"cantidad|EOF"` o `"cantidad"` según si es el último batch
- **Apuestas serializadas**: Cada apuesta en formato `"agency_num/Nombre/Apellido/DNI/Fecha/Numero"`
- **Separadores**: Cada línea separada por `\n`

**Manejo del último batch:**
- **Marcador explícito**: Último batch incluye `|EOF` en la primera línea: `"5|EOF"` vs `"5"`
s

### Ejercicio N°7: Sistema de Sorteo y Consulta de Ganadores

**Solución:** Se implementa un sistema completo de lotería donde las agencias envían apuestas, notifican cuando terminan, y consultan ganadores con estrategia de retry. El servidor realiza el sorteo cuando todas las agencias han notificado y responde consultas de ganadores con manejo de errores.

#### Cómo ejecutar:
```bash
# 1. Levantar el sistema
make docker-compose-up

```

#### Solución implementada:

**Sistema de sorteo:**
- **Sorteo automático**: Se ejecuta cuando todas las agencias notifican `FINISHED`

**Protocolo de comunicación extendido:**
- **FINISHED/agencia**: Notificación de finalización de apuestas
- **QUERY_WINNERS/agencia**: Consulta de ganadores de una agencia
- **Respuestas del servidor**:
  - `FINISHED_ACK`: Confirmación de notificación
  - `WINNERS/agencia/cantidad/dni1,dni2...`: Lista de ganadores
  - `ERROR_403`: Sorteo no realizado aún

**Estrategia "VOLVE PRONTO":**
- **Cierre de conexión**: Cliente cierra socket después de notificar `FINISHED`
- **Nueva conexión**: Se crea conexión independiente para consultar ganadores


**Sistema de retry robusto:**
- **Máximo de reintentos**: 5 intentos con delay de 500ms
- **Reconexión automática**: Nueva conexión TCP para cada intento
- **Manejo de errores específicos**:
  - `ERROR_403`: Sorteo no listo, reintentar

**Flujo completo del sistema:**
1. **Envío de apuestas**: Cliente envía batches de apuestas
2. **Notificación FINISHED**: Cliente notifica finalización
3. **Cierre de conexión**: Cliente cierra socket (VOLVE PRONTO)
4. **Sorteo automático**: Servidor realiza sorteo cuando todas notifican
5. **Consulta de ganadores**: Cliente crea nueva conexión y consulta
6. **Retry inteligente**: Sistema reintenta si sorteo no está listo
7. **Respuesta final**: Servidor devuelve lista de ganadores por agencia


### Ejercicio N°8: Manejo de Concurrencia y Sincronización

**Solución:** Se implementa un servidor multi-threaded que maneja múltiples clientes concurrentemente usando threads de Python y un sistema de locks para proteger secciones críticas. El servidor utiliza un lock principal (`_server_lock`) para sincronizar el acceso a datos compartidos y garantizar la consistencia en el almacenamiento de apuestas y el proceso de sorteo, simulando un barrier al esperar la cantidad de agencias totales conectadas para poder realizar el sorteo.

#### Cómo ejecutar:
```bash

make docker-compose-up

```

#### Solución implementada:

**Arquitectura multi-threaded:**
- **Threads de cliente**: Cada cliente se maneja en un thread independiente
- **Manejo de excepciones**: Cada thread maneja sus propios errores

**Sistema de sincronización:**
- **Lock principal**: `threading.Lock()` para proteger secciones críticas
- **Secciones críticas protegidas**:
  - Modificación del contador de agencias notificadas
  - Verificación y ejecución del sorteo
  - Acceso a datos de ganadores

**Protección de datos compartidos:**
- **Contador de agencias**: `agencias_notificadas`
- **Ganadores por agencia**: `ganadores_por_agencia` (dict protegido)
- **Archivo de apuestas**: Acceso serializado con lock