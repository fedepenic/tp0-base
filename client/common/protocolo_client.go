package common

import (
	"bufio"
	"encoding/csv"
	"fmt"
	"net"
	"os"
	"strings"
)

func (c *Client) SendBets(batchMaxAmount int) {
	agency, err := getAgencyID()
	if err != nil {
		log.Fatalf("error: %v", err)
	}

	bets, err := loadBets(agency)
	if err != nil {
		log.Fatalf("error: %v", err)
	}

	if err := c.initializeConnection(); err != nil {
		log.Fatalf("error: %v", err)
	}
	defer c.cleanup()

	if err := c.sendTotalBets(len(bets)); err != nil {
		log.Fatalf("error: %v", err)
	}

	if err := c.sendBetsInBatches(bets, batchMaxAmount, agency); err != nil {
		log.Fatalf("error: %v", err)
	}

	finalResponse, err := receiveServerResponse(c.conn)
	if err != nil {
		log.Fatalf("error: %v", err)
	}

	log.Infof("Final server response: %s", finalResponse)

	_, err = fmt.Fprintf(c.conn, "FINISHED SENDING BETS\n")
	if err != nil {
		log.Fatalf("error: %v", err)
	}

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

func loadBets(agency string) ([]string, error) {
	filePath := fmt.Sprintf("./.data/agency-%s.csv", agency)
	return readBetsFromFile(filePath)
}

func (c *Client) initializeConnection() error {
	return c.createClientSocket()
}

func (c *Client) sendTotalBets(totalBets int) error {
	_, err := fmt.Fprintf(c.conn, "%d\n", totalBets)
	if err != nil {
		return fmt.Errorf("error sending total bets count: %w", err)
	}
	return expectAcknowledgment(c.conn, "ACK_TOTAL_BETS")
}

func (c *Client) sendBetsInBatches(bets []string, batchMaxAmount int, agency string) error {
	totalBets := len(bets)
	for i := 0; i < totalBets; i += batchMaxAmount {
		end := i + batchMaxAmount
		if end > totalBets {
			end = totalBets
		}

		batch := bets[i:end]
		message := fmt.Sprintf("BATCH_BET:%s|%d|%s\n", agency, batchMaxAmount, strings.Join(batch, ";"))

		if _, err := fmt.Fprintf(c.conn, message); err != nil {
			return fmt.Errorf("error sending batch: %w", err)
		}

		if err := expectAcknowledgment(c.conn, "ACK_BATCH_RECEIVED"); err != nil {
			return err
		}

		log.Infof("action: apuesta_enviada | result: success | batch_size: %d", len(batch))
	}
	return nil
}

func expectAcknowledgment(conn net.Conn, expected string) error {
	ack, err := bufio.NewReader(conn).ReadString('\n')
	if err != nil || strings.TrimSpace(ack) != expected {
		return fmt.Errorf("unexpected acknowledgment: %v", err)
	}
	return nil
}

func receiveServerResponse(conn net.Conn) (string, error) {
	response, err := bufio.NewReader(conn).ReadString('\n')
	if err != nil {
		return "", fmt.Errorf("error receiving final response: %w", err)
	}
	return strings.TrimSpace(response), nil
}

func readBetsFromFile(filePath string) ([]string, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	reader := csv.NewReader(file)
	var bets []string
	for {
		record, err := reader.Read()
		if err != nil {
			break
		}
		if len(record) != 5 {
			continue
		}
		bets = append(bets, strings.Join(record, ","))
	}
	return bets, nil
}

func (c *Client) receiveWinners() error {
	winnersMessage, err := bufio.NewReader(c.conn).ReadString('\n')
	if err != nil {
		return fmt.Errorf("error receiving winners: %w", err)
	}

	winnersMessage = strings.TrimSpace(winnersMessage)

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
