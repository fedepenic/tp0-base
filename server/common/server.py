import socket
import logging
import signal
import sys

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
        # logging.info(f'action: shutdown | result: in_progress | signal: {signum}')
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
                    self.__handle_client_connection(client_sock)
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

    def __accept_new_connection(self):
        """Accept new connections, handling shutdown gracefully."""
        try:
            logging.info('action: accept_connections | result: in_progress')
            c, addr = self._server_socket.accept()
            logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
            return c
        except OSError:
            return None  # Avoid crashing when shutting down

