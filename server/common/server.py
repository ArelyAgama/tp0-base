import socket
import logging
import signal
from common import protocol
from common.utils import store_bets


def store_bet(bet):
    """
    Persist a single bet in the STORAGE_FILEPATH file.
    Required by EJ5 - calls store_bets internally.
    """
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
       
        logging.info('action: SIGTERM_received | result: success | msg: starting_graceful_shutdown')
        self._running = False
        # Cierro el servidor deja de recibir conexiones
        logging.info('action: closing_server_socket | result: success | msg: no_more_connections_accepted')
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
                self.__handle_client_connection(client_sock)
            except OSError:
                # Socket was closed during shutdown
                if client_sock:
                    logging.info('action: closing_client_socket | result: success | msg: connection_terminated_gracefully')
                    client_sock.close()
                break

        logging.info('action: server_shutdown_complete | result: success | msg: all_resources_freed')

        

    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            # Read message using communication protocol (EJ5)
            bet_msg, err = protocol.read_socket(client_sock)
            if err is not None:
                addr = client_sock.getpeername() #get IP and port of the client
                logging.error(f'action: read_socket | result: fail | ip: {addr[0]} | error: {err}')
                return

            # Deserialize message into Bet object (EJ5)
            bet, err = protocol.deserialize(bet_msg)
            if err is not None:
                addr = client_sock.getpeername()
                logging.error(f'action: deserialize | result: fail | ip: {addr[0]} | error: {err}')
                client_sock.close()
                return

            # Store the bet using the required function (EJ5)
            store_bet(bet)
            logging.info(f'action: apuesta_almacenada | result: success | dni: {bet.document} | numero: {bet.number}')

            # Send ACK message back to client (EJ5)
            ack_msg = f'ACK/{bet.agency}/{bet.number}'
            err = protocol.write_socket(client_sock, ack_msg)
            if err is not None:
                addr = client_sock.getpeername()
                logging.error(f'action: send_ack | result: fail | ip: {addr[0]} | error: {err}')
                client_sock.close()
                return
                
        except OSError as e:
            logging.error("action: receive_message | result: fail | error: {e}")
        finally:
            client_sock.close() # Cierro el socket del cliente

        

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
