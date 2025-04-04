import logging
import sys
from common.utils import store_bets, load_bets, has_won, Bet

def __send_message(sock, message):
    sock.sendall(message.encode('utf-8'))

def __receive_message(sock, buffer_size=1024):
    try:
        buffer = b''
        while True:
            chunk = sock.recv(buffer_size)
            if not chunk:
                raise ConnectionError("Socket closed before message was fully received")
            buffer += chunk
            if b'\n' in buffer:
                break
        delimiter_index = buffer.index(b'\n') + 1
        message = buffer[:delimiter_index]
        return message.decode('utf-8')
    except OSError as e:
        logging.error(f"Error receiving data: {e}")
        raise

def handle_bets(lock_file_write, client_sock):
    agency = None
    try:
        __await_start_bets_signal(client_sock)
        number_of_bets_received, agency = __receive_all_batches(lock_file_write, client_sock)
        response = f'Successfully stored {number_of_bets_received} bets for agency {agency}\n'
    except (ValueError, OSError) as e:
        logging.error(f"action: apuesta_recibida | result: fail | cantidad: {number_of_bets_received}")
        response = f'Error processing batch: {str(e)}\n'
    finally:
        __send_final_response(client_sock, response)

    return agency

def __await_start_bets_signal(client_sock):
    message = __receive_message(client_sock)
    if message.strip() != "INICIO_ENVIO_BETS":
        raise ValueError("Expected 'INICIO_ENVIO_BETS' but received something else")
    __acknowledge_client(client_sock, "ACK_INICIO_ENVIO_BETS")

def __receive_all_batches(lock_file_write, client_sock):
    number_of_bets_received = 0
    all_bets_received = False
    agency = None
    while all_bets_received != True:
        bet_batch, batch_agency, all_bets_received = __receive_bet_batch(client_sock)
        if all_bets_received != True:
            number_of_bets_received += len(bet_batch)
            agency = batch_agency
            logging.info(f"Received batch, total bets received: {number_of_bets_received}")
            with lock_file_write:
                __store_received_bets(bet_batch)
            __acknowledge_client(client_sock, "ACK_BATCH_RECEIVED")
    return number_of_bets_received, agency

def __receive_bet_batch(client_sock):
    bet_data = __receive_message(client_sock, 4096)
    if not (bet_data.startswith("BATCH_BET:") or bet_data.startswith("END_OF_BETS")):
        raise ValueError("Invalid batch format")
    if bet_data.startswith("END_OF_BETS"):
        return None, None, True
    else:
        batch_bets, agency = __parse_bet_batch(bet_data[10:])
        return batch_bets, agency, False

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

def process_lottery_results(agency_sockets):
    logging.info('action: sorteo | result: success')
    
    winning_documents = {agency: [] for agency in agency_sockets.keys()}

    for bet in load_bets():
        if has_won(bet):
            winning_documents[str(bet.agency)].append(bet.document)
    
    for agency, documents in winning_documents.items():
        if str(agency) in agency_sockets:
            if not documents:
                winner_message = 'GANADORES: None\n'
            else:
                winner_message = f'GANADORES: {" ,".join(documents)}\n'
            try:
                __send_message(agency_sockets[str(agency)], winner_message)
                logging.info(f'action: send_winners | result: success | agency: {agency} | winners: {winner_message.strip()}')
            except OSError as e:
                logging.error(f'action: send_winners | result: fail | agency: {agency} | error: {e}')

def shutdown(server_socket, agency_sockets, lock_agency_sockets):
    """Handles graceful shutdown of the server."""
    
    server_socket.close()
    
    with lock_agency_sockets:
        for agency_id, client_sock in agency_sockets.items():
            client_sock.close()
    
    logging.info('action: shutdown | result: success')
