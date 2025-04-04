package common

import (
	"bufio"
	"encoding/csv"
	"errors"
	"fmt"
	"io"
	"net"
	"os"
	"strings"
)

func (c *Client) sendMessage(message string) error {
	data := []byte(message)
	totalWritten := 0

	for totalWritten < len(data) {
		n, err := c.conn.Write(data[totalWritten:])
		if err != nil {
			return fmt.Errorf("error sending message: %w", err)
		}
		totalWritten += n
	}

	return nil
}

func readMessage(conn net.Conn) (string, error) {
	message, err := bufio.NewReader(conn).ReadString('\n')
	if err != nil {
		return "", fmt.Errorf("error reading message: %w", err)
	}
	return strings.TrimSpace(message), nil
}

func (c *Client) SendBets(batchMaxAmount int) {
	agency, err := getAgencyID()
	if err != nil {
		log.Fatalf("error: %v", err)
	}

	if err := c.initializeConnection(); err != nil {
		log.Fatalf("error: %v", err)
	}
	defer c.cleanup()

	if err := c.sendBetBatches(batchMaxAmount, agency); err != nil {
		log.Fatalf("error: %v", err)
	}

	finalResponse, err := receiveServerResponse(c.conn)
	if err != nil {
		log.Fatalf("error: %v", err)
	}

	log.Infof("Final server response: %s", finalResponse)

	if err := c.receiveWinners(); err != nil {
		log.Fatalf("error: %v", err)
	}
}

func getAgencyID() (string, error) {
	agency := os.Getenv("CLI_ID")
	if agency == "" {
		return "", fmt.Errorf("missing CLI_ID environment variable")
	}
	return agency, nil
}

func (c *Client) initializeConnection() error {
	return c.createClientSocket()
}

func (c *Client) sendBetBatches(batchMaxAmount int, agency string) error {
	if err := c.sendStartOfBetsMessage(); err != nil {
		return err
	}

	file, err := openCSVFile(agency)
	if err != nil {
		return err
	}
	defer file.Close()

	reader := csv.NewReader(file)
	if err := c.processBets(reader, batchMaxAmount, agency); err != nil {
		return err
	}

	return c.sendEndOfBetsMessage()
}

func (c *Client) sendStartOfBetsMessage() error {
	if err := c.sendMessage("INICIO_ENVIO_BETS\n"); err != nil {
		return fmt.Errorf("error sending start of bets message: %w", err)
	}

	if err := expectAcknowledgment(c.conn, "ACK_INICIO_ENVIO_BETS"); err != nil {
		return fmt.Errorf("error receiving ACK for start of bets: %w", err)
	}

	return nil
}

func openCSVFile(agency string) (*os.File, error) {
	filePath := fmt.Sprintf("./.data/agency-%s.csv", agency)
	file, err := os.Open(filePath)
	if err != nil {
		return nil, fmt.Errorf("error opening file: %w", err)
	}
	return file, nil
}

func (c *Client) processBets(reader *csv.Reader, batchMaxAmount int, agency string) error {
	var batch []string

	for {
		record, err := reader.Read()
		if err != nil {
			if errors.Is(err, io.EOF) {
				return c.flushBatch(batch, batchMaxAmount, agency)
			}
			return fmt.Errorf("error reading file: %w", err)
		}

		if len(record) != 5 {
			continue
		}

		batch = append(batch, strings.Join(record, ","))
		if len(batch) == batchMaxAmount {
			if err := c.sendBatch(batch, batchMaxAmount, agency); err != nil {
				return err
			}
			batch = nil
		}
	}
}

func (c *Client) flushBatch(batch []string, batchMaxAmount int, agency string) error {
	if len(batch) > 0 {
		if err := c.sendBatch(batch, batchMaxAmount, agency); err != nil {
			return err
		}
	}
	return nil
}

func (c *Client) sendEndOfBetsMessage() error {
	if err := c.sendMessage("END_OF_BETS\n"); err != nil {
		return fmt.Errorf("error sending end of bets message: %w", err)
	}
	log.Infof("action: end_of_bets_sent | result: success")
	return nil
}

func (c *Client) sendBatch(batch []string, batchMaxAmount int, agency string) error {
	message := fmt.Sprintf("BATCH_BET:%s|%d|%s\n", agency, batchMaxAmount, strings.Join(batch, ";"))
	if err := c.sendMessage(message); err != nil {
		return fmt.Errorf("error sending batch: %w", err)
	}

	if err := expectAcknowledgment(c.conn, "ACK_BATCH_RECEIVED"); err != nil {
		return fmt.Errorf("error receiving acknowledgment: %w", err)
	}

	log.Infof("action: apuesta_enviada | result: success | batch_size: %d", len(batch))
	return nil
}

func expectAcknowledgment(conn net.Conn, expected string) error {
	ack, err := readMessage(conn)
	if err != nil || ack != expected {
		return fmt.Errorf("unexpected acknowledgment: %v", err)
	}
	return nil
}

func receiveServerResponse(conn net.Conn) (string, error) {
	response, err := readMessage(conn)
	if err != nil {
		return "", fmt.Errorf("error receiving final response: %w", err)
	}
	return response, nil
}

func (c *Client) receiveWinners() error {
	winnersMessage, err := readMessage(c.conn)
	if err != nil {
		return fmt.Errorf("error receiving winners: %w", err)
	}

	const prefix = "GANADORES: "
	if !strings.HasPrefix(winnersMessage, prefix) {
		return fmt.Errorf("unexpected winners message format: %s", winnersMessage)
	}

	winnersList := strings.TrimSpace(strings.TrimPrefix(winnersMessage, prefix))

	if winnersList == "None" {
		winnersList = ""
	}

	var winnersArray []string
	if winnersList != "" {
		winnersArray = strings.Split(winnersList, " ,")
	}

	log.Infof("action: consulta_ganadores | result: success | cant_ganadores: %d", len(winnersArray))

	return nil
}
