package common

import (
	"bufio"
	"fmt"
	"net"
	"os"
	"os/signal"
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
			// Create the connection the server in every loop iteration
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
