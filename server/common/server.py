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
            # Step 1: Receive total number of bets
            total_bets_data = client_sock.recv(1024).decode('utf-8').strip()
            if not total_bets_data.isdigit():
                raise ValueError("Invalid total bets count")
            
            total_bets = int(total_bets_data)
            logging.info(f"Received total bets count: {total_bets}")

            # Send confirmation
            client_sock.sendall(b"ACK_TOTAL_BETS\n")

            bets_received = 0
            all_bets = []

            while bets_received < total_bets:
                # Step 2: Receive a batch
                bet_data = client_sock.recv(4096).rstrip().decode('utf-8')

                if not bet_data.startswith("BATCH_BET:"):
                    raise ValueError("Invalid batch format")

                parts = bet_data[10:].split("|", 2)  # Remove "BATCH_BET:" and split
                if len(parts) != 3:
                    raise ValueError("Batch message must contain 3 parts: agency, batchMaxAmount, and bets")

                agency, batch_max_amount, bets_str = parts
                batch_max_amount = int(batch_max_amount)

                # Parse bets
                batch_bets = []
                for bet_entry in bets_str.split(";"):
                    bet_fields = bet_entry.split(",")
                    bet_fields.insert(0, agency)
                    if len(bet_fields) != 6:
                        logging.warning(f"Skipping invalid bet: {bet_entry}")
                        continue
                    
                    batch_bets.append(Bet(*bet_fields))

                if not batch_bets:
                    raise ValueError("No valid bets found in batch")

                all_bets.extend(batch_bets)
                bets_received += len(batch_bets)

                # Log progress
                logging.info(f"Received batch, total bets received: {bets_received}/{total_bets}")

                # Send acknowledgment for batch
                client_sock.sendall(b"ACK_BATCH_RECEIVED\n")

            # Store the bets after receiving all batches
            store_bets(all_bets)
            logging.info(f"action: apuesta_recibida | result: success | cantidad: {total_bets}")

            response = f'Successfully stored {len(all_bets)} bets\n'

        except (ValueError, OSError) as e:
            logging.error(f"action: apuesta_recibida | result: fail | cantidad: {total_bets}")
            response = f'Error processing batch: {str(e)}\n'

        finally:
            logging.info("Server response: {}".format(str(response)))
            client_sock.sendall(response.encode('utf-8'))
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

