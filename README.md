### Ejercicio N°8: Manejo de Concurrencia y Sincronización

**Solución:** Se implementa un servidor multi-threaded que maneja múltiples clientes concurrentemente usando threads de Python y un sistema de locks para proteger secciones críticas. El servidor utiliza un lock principal (`_server_lock`) para sincronizar el acceso a datos compartidos y garantizar la consistencia en el almacenamiento de apuestas y el proceso de sorteo, simulando un barrier al esperar la cantidad de agencias totales conectadas para poder realizar el sorteo. Se usa multithread porque son operaciones de input output y no de uso intensivo de cpu. Por lo que es valido para el GIL(Global Interpreter Lock) de python.

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