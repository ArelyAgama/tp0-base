import socket
import logging
import signal
from common.utils import store_bets
from common import protocol
from common.protocol import deserialize_batch

# Almacenar 1 apuesta
def store_bet(bet):
    store_bets([bet])

class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #socket IPv4, TCP
        self._server_socket.bind(('', port)) 
        self._server_socket.listen(listen_backlog)
        
        self._running = True
        
        # Manejo en caso de SIGTERM
        signal.signal(signal.SIGTERM, self._handle_sigterm)

    def _handle_sigterm(self, signum, frame):

        logging.info('action: receive_signal | result: success | signal: SIGTERM')
        self._running = False
        # Cierro el servidor deja de recibir conexiones
        logging.info('action: close_server_socket | result: success')
        self._server_socket.close()


    def run(self):
        """
        Server that accept new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        while self._running:
            client_sock = None
            try:
                client_sock = self.__accept_new_connection()
                logging.debug(f"action: client_connected | result: success | about_to_call_handler")
                self.__handle_client_connection(client_sock)
                logging.debug("action: client_handler | result: completed")
            except OSError as e:
                # Socket was closed during shutdown
                logging.error(f"action: client_handler | result: os_error | error: {e}")
                if client_sock:
                    logging.info('action: close_client_socket | result: success')
                    client_sock.close()
                break
            except Exception as e:
                logging.error(f"action: client_handler | result: unexpected_error | error: {e}")
                if client_sock:
                    client_sock.close()

        logging.info('action: server_finished | result: success')
        

    def __handle_client_connection(self, client_sock):
        """
        Maneja la conexión de un cliente procesando múltiples batches de apuestas (EJ6).
        """
        addr = None
        try:
            addr = client_sock.getpeername()
            logging.info(f"action: handle_client_connection | result: starting | ip: {addr[0]}")
            batch_count = 0
            
            # Loop para procesar múltiples batches del mismo cliente
            while True:
                # Leo el mensaje enviado por el cliente usando nuestro protocolo mejorado
                bet_msg, err = protocol.read_socket(client_sock)
                if err is not None:
                    logging.error(f'action: read_socket | result: fail | ip: {addr[0]} | error: {err}')
                    break

                batch_count += 1
                logging.info(f'action: batch_received | result: processing | ip: {addr[0]} | batch_number: {batch_count}')

                # Procesar el batch
                is_last = self.__handle_batch_processing(client_sock, bet_msg)
                
                # Si es el último batch, terminar el loop
                if is_last:
                    logging.info(f'action: all_batches_processed | result: success | ip: {addr[0]} | total_batches: {batch_count}')
                    break

        except Exception as e:
            logging.error(f"action: handle_client_connection | result: error | ip: {addr[0] if addr else 'unknown'} | error: {e}")
        finally:
            if addr:
                logging.info(f"action: close_client_connection | result: success | ip: {addr[0]}")
            client_sock.close()

    def __handle_batch_processing(self, client_sock, bet_msg):
        """Procesa un batch de apuestas. Retorna True si es el último batch """
        try:
            addr = client_sock.getpeername()
            
            # Deserializar el batch
            bets, is_last_batch = deserialize_batch(bet_msg)
            
            logging.info(f"action: batch_received | result: success | ip: {addr[0]} | count: {len(bets)} | is_last: {is_last_batch}")
            
            processed_count = 0
            error_occurred = False
            
            # Procesar cada apuesta del batch
            for bet in bets:
                try:
                    store_bet(bet)
                    processed_count += 1
                    logging.info(f'action: apuesta_almacenada | result: success | dni: {bet.document} | numero: {bet.number}')
                        
                except Exception as e:
                    logging.error(f"action: store_bet | result: fail | bet: {bet} | error: {e}")
                    error_occurred = True
            
            # Si hubo errores, responder con código de error
            if error_occurred:
                response = "ERROR_500"  # Código de error interno del servidor
                logging.error(f"action: apuesta_recibida | result: fail | cantidad: {len(bets)}")
                err = protocol.write_socket(client_sock, response)
                if err is not None:
                    logging.error(f'action: send_error | result: fail | ip: {addr[0]} | error: {err}')
                return is_last_batch
            
            # Respuesta exitosa del batch
            response = f"BATCH_ACK/{processed_count}"
            if is_last_batch:
                response += "/LAST"
                
            logging.info(f"action: batch_processed | result: success | ip: {addr[0]} | processed: {processed_count} | is_last: {is_last_batch}")
            
            err = protocol.write_socket(client_sock, response)
            if err is not None:
                logging.error(f'action: send_batch_ack | result: fail | ip: {addr[0]} | error: {err}')
            
            return is_last_batch
            
        except Exception as e:
            # Error en deserialización o procesamiento general del batch
            try:
                addr = client_sock.getpeername()
                # Si no podemos determinar cuántas apuestas había, usamos 0
                logging.error(f"action: apuesta_recibida | result: fail | cantidad: 0")
                response = "ERROR_400"  # Código de error de formato inválido
                protocol.write_socket(client_sock, response)
            except:
                pass
            logging.error(f"action: process_batch | result: fail | error: {e}")
            return True  # En caso de error, terminar la conexión

        

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        c, addr = self._server_socket.accept() #socket del cliente, address del cliente: IP, puerto
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return c
