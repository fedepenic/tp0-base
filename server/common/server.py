import socket
import logging
import signal
import os
import threading
from common.protocol_server import shutdown, process_lottery_results, handle_bets


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
        agency_id = handle_bets(self, client_sock)
        if agency_id:
            with self._lock_agency_sockets:
                self._agency_sockets[agency_id] = client_sock
    

    def __accept_new_connection(self):
        """Accept new connections, handling shutdown gracefully."""
        try:
            logging.info('action: accept_connections | result: in_progress')
            c, addr = self._server_socket.accept()
            logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
            return c
        except OSError:
            return None
