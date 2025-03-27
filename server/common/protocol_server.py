import logging
import sys


def shutdown(server_socket, agency_sockets, lock_agency_sockets):
    """Handles graceful shutdown of the server."""

    server_socket.close()

    with lock_agency_sockets:
        for agency_id, client_sock in agency_sockets.items():
            client_sock.close()

    logging.info('action: shutdown | result: success')
    sys.exit(0)
