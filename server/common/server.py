import socket
import logging
import signal
import os
import threading
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
        
        # Leer número de agencias desde variable de entorno
        agencias_totales_env = os.getenv("AGENCIAS_TOTALES")
        logging.info(f"AGENCIAS_TOTALES env var: {agencias_totales_env}")
        if agencias_totales_env is None:
            logging.error("AGENCIAS_TOTALES environment variable not set!")
            raise ValueError("AGENCIAS_TOTALES environment variable not set!")
        self.agencias_totales = int(agencias_totales_env)
        
        self.agencias_notificadas = set()
        self.sorteo_realizado = False
        self.ganadores_por_agencia = {}  # Dict: agencia_id -> [dni1, dni2, ...]
        self._server_lock = threading.Lock()  # Lock para proteger secciones críticas
        
        logging.info(f"action: config | result: success | port: {port} | listen_backlog: {listen_backlog} | agencias_totales: {self.agencias_totales}")
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
        communication with a client. Multiple clients can connect
        and be processed in parallel using threads.
        """

        while self._running:
            try:
                client_sock = self.__accept_new_connection()
                logging.debug(f"action: client_connected | result: success | next_action: handle_client")
                
                # Crear thread para manejar cliente (sin tracking - versión simple)
                client_thread = threading.Thread(
                    target=self.__handle_client_connection_extended,
                    args=(client_sock,)
                )
                client_thread.start()
                
            except OSError as e:
                logging.error(f"action: client_handler | result: fail | error: {e}")
                break
            except Exception as e:
                logging.error(f"action: client_handler | result: fail | error: {e}")

        logging.info('action: server_finished | result: success')

    # Maneja la conexión de un cliente procesando múltiples batches de apuestas
    def __handle_client_connection(self, client_sock):
        
        addr = None
        try:
            addr = client_sock.getpeername()
            logging.info(f"action: handle_client_connection | result: in_progress | ip: {addr[0]}")
            batch_count = 0
            
            # Loop para procesar múltiples batches del mismo cliente
            while True:
                bet_msg, err = protocol.read_socket(client_sock)
                if err is not None:
                    logging.error(f'action: read_socket | result: fail | ip: {addr[0]} | error: {err}')
                    break

                batch_count += 1

                is_last = self.__handle_batch_processing(client_sock, bet_msg)
                
                # Si es el último batch, terminar el loop
                if is_last:
                    break

        except Exception as e:
            logging.error(f"action: handle_client_connection | result: error | ip: {addr[0] if addr else 'unknown'} | error: {e}")
        finally:
            if addr:
                logging.info(f"action: close_client_connection | result: success | ip: {addr[0]}")
            client_sock.close()

    # Maneja la conexión de un cliente para notificaciones y consultas
    def __handle_client_connection_extended(self, client_sock):
        
        addr = None
        try:
            addr = client_sock.getpeername()
            logging.info(f"action: handle_client_connection | result: in_progress | ip: {addr[0]}")
            batch_count = 0
            finished_notified = False
            
            # Loop para procesar múltiples mensajes del mismo cliente
            while True:
                msg, err = protocol.read_socket(client_sock)
                if err is not None:
                    logging.error(f'action: read_socket | result: fail | ip: {addr[0]} | error: {err}')
                    break

                # Determinar tipo de mensaje
                if msg.startswith("FINISHED/"):
                    self.__handle_finished_notification(client_sock, msg)
                    finished_notified = True
                    break  # Terminar conexión después de FINISHED (estrategia VOLVE PRONTO)
                elif msg.startswith("QUERY_WINNERS/"):
                    self.__handle_winners_query(client_sock, msg)
                    break  # Terminar después de la consulta
                else:
                    # Es un batch de apuestas
                    batch_count += 1
                    is_last = self.__handle_batch_processing(client_sock, msg)
                    if is_last:
                        # Después del último batch, esperar notificación
                        continue

        except Exception as e:
            logging.error(f"action: handle_client_connection | result: error | ip: {addr[0] if addr else 'unknown'} | error: {e}")
        finally:
            if addr:
                logging.info(f"action: close_client_connection | result: success | ip: {addr[0]}")
            client_sock.close()

    # Deserializa, almacena y valida si es el último batch
    def __handle_batch_processing(self, client_sock, bet_msg):
        try:
            addr = client_sock.getpeername()
            
            # Deserializar el batch
            bets, is_last_batch = deserialize_batch(bet_msg)
            
            processed_count = 0
            error_occurred = False
            
            # Procesar cada apuesta del batch (sección crítica)
            with self._server_lock:
                for bet in bets:
                    try:
                        store_bet(bet)
                        processed_count += 1
                            
                    except Exception as e:
                        error_occurred = True
            
            # Si hubo errores, responder con código de error
            if error_occurred:
                response = "ERROR_500"  # Código de error interno del servidor
                logging.error(f"action: apuesta_recibida | result: fail | cantidad: {len(bets)}")
                err = protocol.write_socket(client_sock, response)
                return is_last_batch
            
            # Log de éxito según especificación
            logging.info(f"action: apuesta_recibida | result: success | cantidad: {len(bets)}")
            
            # Respuesta exitosa del batch
            response = f"BATCH_ACK/{processed_count}"
            if is_last_batch:
                response += "/LAST"
                
            err = protocol.write_socket(client_sock, response)
            
            return is_last_batch
            
        except Exception as e:
            # Error en deserialización o procesamiento general del batch
            try:
                addr = client_sock.getpeername()
                logging.error(f"action: apuesta_recibida | result: fail | cantidad: 0")
                response = "ERROR_400"  # Código de error de formato inválido
                protocol.write_socket(client_sock, response)
            except:
                pass
            logging.error(f"action: process_batch | result: fail | error: {e}")
            return True  # En caso de error, terminar la conexión

    # Maneja la notificación de finalización de apuestas de una agencia
    def __handle_finished_notification(self, client_sock, msg):
        try:
            addr = client_sock.getpeername()
            # Parsear mensaje: "FINISHED/agencia"
            parts = msg.split('/')
            if len(parts) != 2:
                logging.error(f"action: parse_finished_notification | result: fail | ip: {addr[0]} | msg: {msg}")
                protocol.write_socket(client_sock, "ERROR_400")
                return
            
            agencia = parts[1]
            
            # Sección crítica: modificar contador de agencias y verificar sorteo
            with self._server_lock:
                self.agencias_notificadas.add(agencia)
                
                logging.info(f"action: agency_finished | result: success | agency: {agencia} | total_notified: {len(self.agencias_notificadas)}")
                
                # Verificar si todas las agencias esperadas han notificado
                if len(self.agencias_notificadas) == self.agencias_totales:
                    self.__perform_lottery()
            
            # Responder confirmación (fuera del lock)
            protocol.write_socket(client_sock, "FINISHED_ACK")
                
        except Exception as e:
            logging.error(f"action: handle_finished_notification | result: fail | error: {e}")
            try:
                protocol.write_socket(client_sock, "ERROR_500")
            except:
                pass

    # Maneja la consulta de ganadores de una agencia
    def __handle_winners_query(self, client_sock, msg):
        try:
            addr = client_sock.getpeername()
            # Parsear mensaje: "QUERY_WINNERS/agencia"
            parts = msg.split('/')
            if len(parts) != 2:
                logging.error(f"action: parse_winners_query | result: fail | ip: {addr[0]} | msg: {msg}")
                protocol.write_socket(client_sock, "ERROR_400")
                return
            
            agencia = parts[1]
            
            # Sección crítica: verificar estado del sorteo y obtener ganadores
            with self._server_lock:
                # Verificar que el sorteo ya se haya realizado
                if not self.sorteo_realizado:
                    logging.info(f"lottery_not_ready | agency: {agencia} | waiting_for_lottery")
                    protocol.write_socket(client_sock, "ERROR_403")  # Forbidden - sorteo no realizado
                    return
                
                # Obtener ganadores de la agencia
                ganadores = self.ganadores_por_agencia.get(agencia, [])
                cant_ganadores = len(ganadores)
            
            # Formatear respuesta: "WINNERS/agencia/cantidad/dni1,dni2,dni3..."
            if cant_ganadores > 0:
                dnis = ','.join(ganadores)
                response = f"WINNERS/{agencia}/{cant_ganadores}/{dnis}"
            else:
                response = f"WINNERS/{agencia}/0/"
            
            protocol.write_socket(client_sock, response)
            logging.info(f"action: winners_query | result: success | agency: {agencia} | winners: {cant_ganadores}")
            
        except Exception as e:
            logging.error(f"action: handle_winners_query | result: fail | error: {e}")
            try:
                protocol.write_socket(client_sock, "ERROR_500")
            except:
                pass

    # Realiza el sorteo cuando todas las agencias han notificado
    def __perform_lottery(self):
        try:
            logging.info("action: sorteo | result: success")
            self.sorteo_realizado = True
            
            # Cargar todas las apuestas y verificar ganadores
            from common.utils import load_bets, has_won
            
            for bet in load_bets():
                if has_won(bet):
                    agencia_str = str(bet.agency)
                    if agencia_str not in self.ganadores_por_agencia:
                        self.ganadores_por_agencia[agencia_str] = []
                    self.ganadores_por_agencia[agencia_str].append(bet.document)
            
            # Log de resumen
            total_ganadores = sum(len(ganadores) for ganadores in self.ganadores_por_agencia.values())
            logging.info(f"action: lottery_completed | result: success | total_winners: {total_ganadores}")
            
        except Exception as e:
            logging.error(f"action: perform_lottery | result: fail | error: {e}")

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
