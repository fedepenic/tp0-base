import logging
import sys
from common.utils import store_bets, load_bets, has_won, Bet

def __send_message(sock, message):
    sock.sendall(message.encode('utf-8'))

def handle_bets(server, client_sock):
    agency = None
    try:
        number_of_bets = __receive_number_of_bets(client_sock)
        all_bets, agency = __receive_all_batches(client_sock, number_of_bets)
        __store_received_bets(all_bets)

        with server._lock_completed_agencies:
            server._completed_agencies.add(agency)

        response = f'Successfully stored {len(all_bets)} bets for agency {agency}\n'
    except (ValueError, OSError) as e:
        logging.error(f"action: apuesta_recibida | result: fail | cantidad: {number_of_bets}")
        response = f'Error processing batch: {str(e)}\n'
    finally:
        __send_final_response(client_sock, response)
    
    finished_sending_bets_msg = client_sock.recv(1024).rstrip().decode('utf-8')

    logging.info(f'Agency {agency} message: {finished_sending_bets_msg} ')

    return agency

def __receive_number_of_bets(client_sock):
    total_bets_data = client_sock.recv(1024).decode('utf-8').strip()
    if not total_bets_data.isdigit():
        raise ValueError("Invalid total bets count")
    total_bets = int(total_bets_data)
    logging.info(f"Received total bets count: {total_bets}")
    __acknowledge_client(client_sock, "ACK_TOTAL_BETS")
    return total_bets

def __receive_all_batches(client_sock, total_bets):
    bets_received = 0
    all_bets = []
    agency = None
    while bets_received < total_bets:
        batch_bets, batch_agency = __receive_bet_batch(client_sock)
        all_bets.extend(batch_bets)
        bets_received += len(batch_bets)
        agency = batch_agency
        logging.info(f"Received batch, total bets received: {bets_received}/{total_bets}")
        __acknowledge_client(client_sock, "ACK_BATCH_RECEIVED")
    return all_bets, agency

def __receive_bet_batch(client_sock):
    bet_data = client_sock.recv(4096).rstrip().decode('utf-8')
    if not bet_data.startswith("BATCH_BET:"):
        raise ValueError("Invalid batch format")
    return __parse_bet_batch(bet_data[10:])

def __parse_bet_batch(batch_data):
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

def __acknowledge_client(client_sock, message):
    __send_message(client_sock, f"{message}\n")

def __store_received_bets(bets):
    store_bets(bets)
    logging.info(f"action: apuesta_recibida | result: success | cantidad: {len(bets)}")

def __send_final_response(client_sock, response):
    logging.info(f"Server response: {response.strip()}")
    __send_message(client_sock, response)

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
                    __send_message(server._agency_sockets[str(agency)], winner_message)
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