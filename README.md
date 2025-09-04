### Ejercicio N°4: Manejo Graceful de SIGTERM

**Solución:** Se implementa el manejo de la señal SIGTERM tanto en el cliente como en el servidor para permitir un cierre graceful de las aplicaciones, cerrando correctamente todos los recursos (sockets, conexiones) y loggeando cada paso del proceso de shutdown, usando un channel para recibir SIGTERM del lado del cliente y un handler de signals del lado del servidor.

#### Cómo ejecutar:
```bash
make docker-compose-up

```

