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
        signal.signal(signal.SIGTERM, self.__shutdown)
        signal.signal(signal.SIGINT, self.__shutdown)

    def __shutdown(self, signum, frame):
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
                    self.__handle_bets(client_sock)
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

    def __handle_bets(self, client_sock):
        """Handles the reception, validation, and storage of bets from a client."""
        try:
            number_of_bets = self.__receive_number_of_bets(client_sock)
            all_bets = self.__receive_all_batches(client_sock, number_of_bets)
            self.__store_received_bets(all_bets)
            response = f'Successfully stored {len(all_bets)} bets\n'
        except (ValueError, OSError) as e:
            logging.error(f"action: apuesta_recibida | result: fail | cantidad: {number_of_bets}")
            response = f'Error processing batch: {str(e)}\n'
        finally:
            self.__send_final_response(client_sock, response)

    def __receive_number_of_bets(self, client_sock):
        """Receives the total number of bets from the client."""
        total_bets_data = client_sock.recv(1024).decode('utf-8').strip()
        if not total_bets_data.isdigit():
            raise ValueError("Invalid total bets count")

        total_bets = int(total_bets_data)
        logging.info(f"Received total bets count: {total_bets}")
        self.__acknowledge_client(client_sock, "ACK_TOTAL_BETS")
        return total_bets

    def __receive_all_batches(self, client_sock, total_bets):
        """Receives batches of bets until the expected total is met."""
        bets_received = 0
        all_bets = []

        while bets_received < total_bets:
            batch_bets = self.__receive_bet_batch(client_sock)
            all_bets.extend(batch_bets)
            bets_received += len(batch_bets)
            logging.info(f"Received batch, total bets received: {bets_received}/{total_bets}")
            self.__acknowledge_client(client_sock, "ACK_BATCH_RECEIVED")

        return all_bets

    def __receive_bet_batch(self, client_sock):
        """Receives and parses a single batch of bets."""
        bet_data = client_sock.recv(4096).rstrip().decode('utf-8')

        if not bet_data.startswith("BATCH_BET:"):
            raise ValueError("Invalid batch format")

        return self.__parse_bet_batch(bet_data[10:])

    def __parse_bet_batch(self, batch_data):
        """Parses a batch of bets from the received message."""
        parts = batch_data.split("|", 2)
        if len(parts) != 3:
            raise ValueError("Batch message must contain 3 parts: agency, batchMaxAmount, and bets")

        agency, batch_max_amount, bets_str = parts
        batch_max_amount = int(batch_max_amount)

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

        return batch_bets

    def __acknowledge_client(self, client_sock, message):
        """Sends an acknowledgment message to the client."""
        client_sock.sendall(f"{message}\n".encode('utf-8'))

    def __store_received_bets(self, bets):
        """Stores the received bets."""
        store_bets(bets)
        logging.info(f"action: apuesta_recibida | result: success | cantidad: {len(bets)}")

    def __send_final_response(self, client_sock, response):
        """Sends the final response to the client and closes the connection."""
        logging.info(f"Server response: {response.strip()}")
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

