import socket
import logging
import signal
import os
import threading
from common.protocol_server import shutdown, process_lottery_results
from common.utils import store_bets, Bet


class Server:
    def __init__(self, port, listen_backlog):
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._running = True
        self._completed_agencies = set()
        self._total_agencies = int(os.getenv("CANTIDAD_CLIENTES", 0))
        self._agency_sockets = {}

        self._lock_completed_agencies = threading.Lock()
        self._lock_agency_sockets = threading.Lock()

        signal.signal(signal.SIGTERM, self.__handle_shutdown)
        signal.signal(signal.SIGINT, self.__handle_shutdown)

    def __handle_shutdown(self, signum, frame):
        self._running = False
        shutdown(self._server_socket, self._agency_sockets, self._lock_agency_sockets)

    def run(self):
        thread_counter = 0
        while self._running:
            try:
                client_sock = self.__accept_new_connection()
                if client_sock:
                    threading.Thread(target=self.__handle_new_client, args=(client_sock,), daemon=True).start()
                    thread_counter += 1
                if thread_counter >= self._total_agencies:
                    while self._running:
                        process_lottery_results(self)
            except OSError as e:
                logging.error(f"action: run | result: failure | error: {e} | description: Error handling new connection or processing lottery results")
                self.__handle_shutdown(None, None)
        
        self.__handle_shutdown(None, None)

    def __handle_new_client(self, client_sock):
        agency_id = self.__handle_bets(client_sock)
        msg = client_sock.recv(1024).rstrip().decode('utf-8')
        if agency_id:
            with self._lock_agency_sockets:
                self._agency_sockets[agency_id] = client_sock
    

    def __handle_bets(self, client_sock):
        agency = None
        try:
            number_of_bets = self.__receive_number_of_bets(client_sock)
            all_bets, agency = self.__receive_all_batches(client_sock, number_of_bets)
            self.__store_received_bets(all_bets)

            with self._lock_completed_agencies:
                self._completed_agencies.add(agency)

            response = f'Successfully stored {len(all_bets)} bets for agency {agency}\n'
        except (ValueError, OSError) as e:
            logging.error(f"action: apuesta_recibida | result: fail | cantidad: {number_of_bets}")
            response = f'Error processing batch: {str(e)}\n'
        finally:
            self.__send_final_response(client_sock, response)
        return agency

    def __receive_number_of_bets(self, client_sock):
        total_bets_data = client_sock.recv(1024).decode('utf-8').strip()
        if not total_bets_data.isdigit():
            raise ValueError("Invalid total bets count")
        total_bets = int(total_bets_data)
        logging.info(f"Received total bets count: {total_bets}")
        self.__acknowledge_client(client_sock, "ACK_TOTAL_BETS")
        return total_bets

    def __receive_all_batches(self, client_sock, total_bets):
        bets_received = 0
        all_bets = []
        agency = None
        while bets_received < total_bets:
            batch_bets, batch_agency = self.__receive_bet_batch(client_sock)
            all_bets.extend(batch_bets)
            bets_received += len(batch_bets)
            agency = batch_agency
            logging.info(f"Received batch, total bets received: {bets_received}/{total_bets}")
            self.__acknowledge_client(client_sock, "ACK_BATCH_RECEIVED")
        return all_bets, agency

    def __receive_bet_batch(self, client_sock):
        bet_data = client_sock.recv(4096).rstrip().decode('utf-8')
        if not bet_data.startswith("BATCH_BET:"):
            raise ValueError("Invalid batch format")
        return self.__parse_bet_batch(bet_data[10:])

    def __parse_bet_batch(self, batch_data):
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
        return batch_bets, agency

    def __acknowledge_client(self, client_sock, message):
        client_sock.sendall(f"{message}\n".encode('utf-8'))

    def __store_received_bets(self, bets):
        store_bets(bets)
        logging.info(f"action: apuesta_recibida | result: success | cantidad: {len(bets)}")

    def __send_final_response(self, client_sock, response):
        logging.info(f"Server response: {response.strip()}")
        client_sock.sendall(response.encode('utf-8'))

    def __accept_new_connection(self):
        """Accept new connections, handling shutdown gracefully."""
        try:
            logging.info('action: accept_connections | result: in_progress')
            c, addr = self._server_socket.accept()
            logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
            return c
        except OSError:
            return None
