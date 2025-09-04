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

