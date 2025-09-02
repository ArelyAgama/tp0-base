import logging
from common.utils import Bet

HEADER_LENGHT = 4

# Campos del mensaje de apuesta
AGENCY= 0
NAME= 1
SURNAME = 2
DOCUMENT= 3
BIRTH= 4
NUMBER= 5

# Deserializa un mensaje y crea una apuesta.
def deserialize(msg):
    splitted_msg = msg.split('/')

    agency = splitted_msg[AGENCY]
    name = splitted_msg[NAME]
    surname = splitted_msg[SURNAME]
    document = splitted_msg[DOCUMENT]
    birth= splitted_msg[BIRTH]
    number = splitted_msg[NUMBER]

    try:
        return (Bet(agency,
                    name,
                    surname,
                    document,
                    birth,
                    number),
                    None)
    except ValueError as e:
        return (None, e)

# Valida que se lea el mensaje completo
def _handle_short_read(socket, total_bytes_to_read):
    bytes_read = 0
    msg = ""
    while bytes_read < total_bytes_to_read:
        data = socket.recv(total_bytes_to_read - bytes_read)
        if not data:
            break
        decoded_data = data.decode('utf-8')
        msg += decoded_data
        bytes_read += len(decoded_data)
    return msg

# Leo del socket validando con handle short-read
def read_socket(socket):
    try: 
        header = _handle_short_read(socket, HEADER_LENGHT)
        msg_len = int(header)

        bet_msg = _handle_short_read(socket, msg_len)
        return bet_msg, None
    
    except Exception as e:
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

    for _ in range(0, HEADER_LENGHT - msg_len_bytes):
        msg_len = '0' + msg_len

    return msg_len
