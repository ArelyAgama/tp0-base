import socket
import logging
import signal


class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #socket IPv4, TCP
        self._server_socket.bind(('', port)) 
        self._server_socket.listen(listen_backlog)
        
        # Variable to control server loop
        self._running = True
        
        # Configure signal handler for SIGTERM
        signal.signal(signal.SIGTERM, self._handle_sigterm)

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
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
                    logging.info('action: close_client_socket | result: success')
                    client_sock.close()
                break

        #Doble check de que este cerrado el socket
        try:
            self._server_socket.close()
        except OSError:
            pass

        logging.info('action: server_finished | result: success')

    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            # TODO: Modify the receive to avoid short-reads
            msg = client_sock.recv(1024).rstrip().decode('utf-8')
            addr = client_sock.getpeername() #get IP and port of the client
            logging.info(f'action: receive_message | result: success | ip: {addr[0]} | msg: {msg}') #IP del cliente y el mensaje de hasta 1024 bytes
            # TODO: Modify the send to avoid short-writes
            client_sock.send("{}\n".format(msg).encode('utf-8'))
        except OSError as e:
            logging.error("action: receive_message | result: fail | error: {e}")
        finally:
            client_sock.close()

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

    def _handle_sigterm(self, signum, frame):
        """
        Handle SIGTERM signal for graceful shutdown
        """
        logging.info('action: receive_signal | result: success | signal: SIGTERM')
        self._running = False
        # Close server socket to stop accepting new connections
        logging.info('action: close_server_socket | result: success')
        self._server_socket.close()
