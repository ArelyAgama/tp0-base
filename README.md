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