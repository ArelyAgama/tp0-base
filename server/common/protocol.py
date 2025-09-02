import logging
from common.utils import Bet

HEADER_LENGTH= 4

# Campos del mensaje de apuesta
AGENCY= 0
NAME= 1
SURNAME = 2
DOCUMENT= 3
BIRTH= 4
NUMBER= 5

# Deserializa un mensaje de batch y retorna lista de apuestas y si es el último batch
def deserialize_batch(msg):
    lines = msg.strip().split('\n')
    if len(lines) < 1:
        raise ValueError("Empty batch message")
    
    # Primera línea: cantidad de apuestas (y posible EOF marker)
    first_line = lines[0]
    is_last_batch = False
    
    if '|EOF' in first_line:
        count_str = first_line.split('|')[0]
        is_last_batch = True
    else:
        count_str = first_line
    
    try:
        expected_count = int(count_str)
    except ValueError:
        raise ValueError(f"Invalid batch count: {first_line}")
    
    # Verificar que tenemos la cantidad correcta de líneas
    actual_count = len(lines) - 1  # -1 porque la primera línea es el contador
    if actual_count != expected_count:
        raise ValueError(f"Expected {expected_count} bets, got {actual_count}")
    
    # Deserializar cada apuesta
    bets = []
    for i in range(1, len(lines)):
        line = lines[i].strip()
        if not line:  # Saltar líneas vacías
            continue
            
        bet = deserialize_single_bet(line)
        bets.append(bet)
    
    return bets, is_last_batch

# Deserializa una sola apuesta (función auxiliar)
def deserialize_single_bet(msg):
    splitted_msg = msg.split('/')
    
    if len(splitted_msg) != 6:
        raise ValueError(f"Invalid bet format: expected 6 fields, got {len(splitted_msg)}")

    agency = splitted_msg[AGENCY]
    name = splitted_msg[NAME]
    surname = splitted_msg[SURNAME]
    document = splitted_msg[DOCUMENT]
    birth = splitted_msg[BIRTH]
    number = splitted_msg[NUMBER]

    try:
        return Bet(agency, name, surname, document, birth, number)
    except Exception as e:
        raise ValueError(f"Error creating bet: {e}")

# Deserializa un mensaje y crea una apuesta (función legacy para EJ5)
def deserialize(msg):
    return deserialize_single_bet(msg)

# Valida que se lea el mensaje completo
def _handle_short_read(socket, total_bytes_to_read):
    bytes_read = 0
    msg = ""
    
    while bytes_read < total_bytes_to_read:
        try:
            data = socket.recv(total_bytes_to_read - bytes_read)
            if not data:
                break
            
            # Usar encoding con error handling para manejar caracteres especiales
            decoded_data = data.decode('utf-8', errors='ignore')
            msg += decoded_data
            bytes_read += len(data)  # Contar bytes originales, no caracteres decodificados
            
        except UnicodeDecodeError as e:
            logging.error(f"action: handle_short_read | result: fail | error: {e} | bytes_read: {bytes_read}")
            # Intentar con latin-1 que acepta cualquier byte
            decoded_data = data.decode('latin-1')
            msg += decoded_data
            bytes_read += len(data)
            
    return msg

# Leo del socket validando con handle short-read
def read_socket(socket):
    try: 
        header = _handle_short_read(socket, HEADER_LENGTH)
        
        msg_len = int(header)

        bet_msg = _handle_short_read(socket, msg_len)
        
        return bet_msg, None
    
    except Exception as e:
        logging.error(f"action: read_socket | result: fail | error: {e}")
        return None, e

# Escribo en el socket validando con handle short-write
def write_socket(socket, msg):
    try: 
        header = get_header(msg)
        complete_msg = header + msg
        _handle_short_write(socket, complete_msg, len(complete_msg))
        return None
    except Exception as e:
        return e

# Valida que se escriba el mensaje completo
def _handle_short_write(socket, msg, total_bytes_to_write):
    msg_bytes = msg.encode("utf-8")
    sent_bytes = 0
    while sent_bytes < total_bytes_to_write:
        sent = socket.send(msg_bytes[sent_bytes:])
        if sent == 0:
            raise RuntimeError("Socket connection broken")
        sent_bytes += sent

# Tamaño del header como string
def get_header(msg):
    msg_len = str(len(msg))
    msg_len_bytes = len(msg_len)

    for _ in range(0, HEADER_LENGTH - msg_len_bytes):
        msg_len = '0' + msg_len

    return msg_len
