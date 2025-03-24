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

// SendBets envía las apuestas en lotes de tamaño batchMaxAmount
func (c *Client) SendBets(batchMaxAmount int) {
	// Obtener CLI_ID desde variable de entorno
	agency := os.Getenv("CLI_ID")
	if agency == "" {
		log.Fatalf("error: missing CLI_ID environment variable")
	}

	// Leer apuestas desde el archivo CSV
	filePath := fmt.Sprintf("./.data/agency-%s.csv", agency)
	bets, err := readBetsFromFile(filePath)
	if err != nil {
		log.Fatalf("error reading bets file: %v", err)
	}

	// Crear socket del cliente
	if err := c.createClientSocket(); err != nil {
		log.Fatalf("error creating socket: %v", err)
	}
	defer c.conn.Close()

	// Enviar apuestas en lotes de tamaño batchMaxAmount
	for i := 0; i < len(bets); i += batchMaxAmount {
		end := i + batchMaxAmount
		if end > len(bets) {
			end = len(bets)
		}

		// Formato del mensaje: BATCH_BET:agency|maxAmount|bet1;bet2;...
		batch := bets[i:end]
		message := fmt.Sprintf("BATCH_BET:%s|%d|%s\n", agency, batchMaxAmount, strings.Join(batch, ";"))

		// Enviar batch al servidor
		_, err := fmt.Fprintf(c.conn, message)
		if err != nil {
			log.Fatalf("error sending batch: %v", err)
		}

		// Recibir respuesta del servidor
		_, err = bufio.NewReader(c.conn).ReadString('\n')
		if err != nil {
			log.Fatalf("error receiving response: %v", err)
		}

		log.Infof("action: apuesta_enviada | result: success | batch_size: %d", len(batch))
	}
}

// readBetsFromFile lee las apuestas del archivo CSV
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

