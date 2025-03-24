import socket
import logging
import signal
import sys
from common.utils import store_bets, Bet


class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self.running = True  # Flag to control the main loop

        # Register signal handlers
        signal.signal(signal.SIGTERM, self._shutdown)
        signal.signal(signal.SIGINT, self._shutdown)

    def _shutdown(self, signum, frame):
        """Handle termination signals to gracefully shut down the server."""
        # logging.info(f'action: shutdown | result: in_progress 
        # | signal: {signum}')
        self.running = False
        self._server_socket.close()
        logging.info('action: shutdown | result: success')
        sys.exit(0)

    def run(self):
        """
        Dummy Server loop

        Server that accepts new connections and establishes a
        communication with a client. After a client finishes communication,
        the server starts accepting new connections again.
        """

        while self.running:
            try:
                client_sock = self.__accept_new_connection()
                if client_sock:
                    # self.__handle_client_connection(client_sock)
                    self.__handle_bet(client_sock)
            except OSError:
                break  # Stop accepting connections when shutting down

    def __handle_client_connection(self, client_sock):
        """Read message from a specific client socket and close the socket."""
        try:
            msg = client_sock.recv(1024).rstrip().decode('utf-8')
            addr = client_sock.getpeername()
            logging.info(f'action: receive_message | result: success | ip: {addr[0]} | msg: {msg}')
            client_sock.send("{}\n".format(msg).encode('utf-8'))
        except OSError as e:
            logging.error(f"action: receive_message | result: fail | error: {e}")
        finally:
            client_sock.close()

    def __handle_bet(self, client_sock):
        """Receive, process, and store a batch of bets from a client socket."""
        try:
            bet_data = client_sock.recv(4096).rstrip().decode('utf-8')  # Aumentamos el buffer para manejar batches más grandes
            
            # Expected format: "BATCH_BET:agency|maxAmount|bet1;bet2;..."
            if not bet_data.startswith("BATCH_BET:"):
                raise ValueError("Invalid batch format")

            # Parse message
            parts = bet_data[10:].split("|", 2)  # Removemos "BATCH_BET:" y dividimos en 3 partes
            if len(parts) != 3:
                logging.error(f"action: apuesta_recibida | result: fail | cantidad: {len(bets)}")
                raise ValueError("Batch message must contain 3 parts: agency, batchMaxAmount, and bets")

            agency, batch_max_amount, bets_str = parts
            batch_max_amount = int(batch_max_amount)  # Convertir el maxAmount a entero

            # Parse bets
            bets = []
            for bet_entry in bets_str.split(";"):
                bet_fields = bet_entry.split(",")
                bet_fields.insert(0, agency)
                if len(bet_fields) != 6:
                    logging.warning(f"Skipping invalid bet: {bet_entry}")
                    continue  # Omitimos apuestas mal formateadas
                
                bets.append(Bet(*bet_fields))

            if not bets:
                raise ValueError("No valid bets found in batch")

            # Store the bets
            store_bets(bets)

            # Log success
            logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')

            response = f'success\n'

        except (ValueError, OSError) as e:
            logging.error(f"action: apuestas_almacenadas | result: fail | error: {e}")
            response = f'Error processing batch: {str(e)}\n'

        finally:
            client_sock.send(response.encode('utf-8'))
            client_sock.close()


    def __accept_new_connection(self):
        """Accept new connections, handling shutdown gracefully."""
        try:
            logging.info('action: accept_connections | result: in_progress')
            c, addr = self._server_socket.accept()
            logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
            return c
        except OSError:
            return None  # Avoid crashing when shutting down

