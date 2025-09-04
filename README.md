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