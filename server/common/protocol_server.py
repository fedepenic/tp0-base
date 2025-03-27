import logging
import sys
from common.utils import load_bets, has_won


def process_lottery_results(server):
    if (len(server._completed_agencies) >= server._total_agencies and len(server._agency_sockets) >= server._total_agencies):
        logging.info('action: sorteo | result: success')
        
        winning_documents = {agency: [] for agency in server._completed_agencies}

        for bet in load_bets():
            if has_won(bet):
                winning_documents[str(bet.agency)].append(bet.document)
        
        for agency, documents in winning_documents.items():
            if str(agency) in server._agency_sockets:
                if not documents:
                    winner_message = 'GANADORES: None\n'
                else:
                    winner_message = f'GANADORES: {" ,".join(documents)}\n'
                try:
                    server._agency_sockets[str(agency)].sendall(winner_message.encode('utf-8'))
                    logging.info(f'action: send_winners | result: success | agency: {agency} | winners: {winner_message.strip()}')
                except OSError as e:
                    logging.error(f'action: send_winners | result: fail | agency: {agency} | error: {e}')
        server._running = False


def shutdown(server_socket, agency_sockets, lock_agency_sockets):
    """Handles graceful shutdown of the server."""

    server_socket.close()

    with lock_agency_sockets:
        for agency_id, client_sock in agency_sockets.items():
            client_sock.close()

    logging.info('action: shutdown | result: success')
    sys.exit(0)
