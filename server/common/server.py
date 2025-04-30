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
        self._total_agencies = int(os.getenv("CANTIDAD_CLIENTES", 0))
        self._agency_sockets = {}
        self._threads = []

        self._lock_agency_sockets = threading.Lock()
        self._lock_file_write = threading.Lock()

        signal.signal(signal.SIGTERM, self.__handle_shutdown)
        signal.signal(signal.SIGINT, self.__handle_shutdown)

    def __handle_shutdown(self, signum, frame):
        self._running = False
        shutdown(self._server_socket, self._agency_sockets, self._lock_agency_sockets)

        for thread in self._threads:
            thread.join()

    def run(self):
        while self._running:
            try:
                client_sock = self.__accept_new_connection()
                if client_sock:
                    new_thread = threading.Thread(target=self.__handle_new_client, args=(client_sock,))
                    new_thread.start()
                    self._threads.append(new_thread)
                
                if len(self._threads) >= self._total_agencies:
                    for thread in self._threads:
                        thread.join()

                    process_lottery_results(self._agency_sockets)
                    self._running = False

            except OSError as e:
                logging.error(f"action: run | result: failure | error: {e} | description: Error handling new connection or processing lottery results")
                self.__handle_shutdown(None, None)

        self.__handle_shutdown(None, None)

    def __handle_new_client(self, client_sock):
        try:
            agency_id = handle_bets(self._lock_file_write, client_sock)
            if agency_id:
                with self._lock_agency_sockets:
                    self._agency_sockets[agency_id] = client_sock
                    return
        finally:
            if client_sock not in self._agency_sockets.values():
                client_sock.close()

    def __accept_new_connection(self):
        """Accept new connections, handling shutdown gracefully."""
        try:
            logging.info('action: accept_connections | result: in_progress')
            c, addr = self._server_socket.accept()
            logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
            return c
        except OSError:
            return None
