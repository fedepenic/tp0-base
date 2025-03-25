package common

import (
	"bufio"
	"encoding/csv"
	"fmt"
	"net"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
}

// Client Entity that encapsulates how
type Client struct {
	config ClientConfig
	conn   net.Conn
	stopCh chan struct{} // Channel to signal termination
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	client := &Client{
		config: config,
		stopCh: make(chan struct{}), // Initialize stop channel
	}

	// Handle system signals for graceful shutdown
	go client.handleSignals()

	return client
}

// CreateClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
func (c *Client) createClientSocket() error {
	conn, err := net.Dial("tcp", c.config.ServerAddress)
	if err != nil {
		log.Criticalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return err
	}
	c.conn = conn
	return nil
}

// handleSignals listens for termination signals and ensures resources are cleaned up
func (c *Client) handleSignals() {
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

	<-sigCh // Wait for a termination signal

	// log.Warningf("action: termination_signal | result: received | client_id: %v", c.config.ID)
	c.cleanup()
	os.Exit(0)
}

// cleanup closes the client connection gracefully
func (c *Client) cleanup() {
	if c.conn != nil {
		// log.Infof("action: cleanup | result: closing_connection | client_id: %v", c.config.ID)
		c.conn.Close()
	}
	close(c.stopCh) // Signal to stop processing
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop() {
	for msgID := 1; msgID <= c.config.LoopAmount; msgID++ {
		select {
		case <-c.stopCh:
			log.Warningf("action: loop_interrupted | result: stopped | client_id: %v", c.config.ID)
			return
		default:
			// Create the connection to the server in every loop iteration
			if err := c.createClientSocket(); err != nil {
				return
			}

			// TODO: Modify the send to avoid short-write
			fmt.Fprintf(
				c.conn,
				"[CLIENT %v] Message N°%v\n",
				c.config.ID,
				msgID,
			)
			msg, err := bufio.NewReader(c.conn).ReadString('\n')
			c.conn.Close()

			if err != nil {
				log.Errorf("action: receive_message | result: fail | client_id: %v | error: %v",
					c.config.ID,
					err,
				)
				return
			}

			log.Infof("action: receive_message | result: success | client_id: %v | msg: %v",
				c.config.ID,
				msg,
			)

			// Wait a time between sending one message and the next one
			time.Sleep(c.config.LoopPeriod)
		}
	}
	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}

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

