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
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	client := &Client{
		config: config,
	}
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
	}
	c.conn = conn
	return nil
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop() {
	// autoincremental msgID to identify every message sent
	msgID := 1

	// Channel to receive SIGTERM signal
	signalChan := make(chan os.Signal, 1)
	signal.Notify(signalChan, syscall.SIGTERM)

	// Envio de mensajes
	for i := 0; i < c.config.LoopAmount; i++ {
		// Envio de mensaje
		if !c.sendSingleMessage(msgID, signalChan) {
			return // en caso de error o SIGTERM
		}
		msgID++

		// SIGTERM o timeout
		select {
		case <-signalChan:
			log.Infof("action: SIGTERM_received | result: success | client_id: %v | msg: stopping_gracefully", c.config.ID)
			return
		case <-time.After(c.config.LoopPeriod):
			// Continua
		}
	}

	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}

// sendSingleMessage handles one complete message exchange with SIGTERM awareness
func (c *Client) sendSingleMessage(msgID int, signalChan <-chan os.Signal) bool {
	// Creo la conexión
	err := c.createClientSocket()
	if err != nil {
		log.Errorf("action: create_socket | result: fail | client_id: %v | error: %v", c.config.ID, err)
		return false
	}
	defer func() {
		if c.conn != nil {
			log.Infof("action: closing_connection | result: success | client_id: %v", c.config.ID)
			c.conn.Close()
		}
	}() // cierro la conexión al final de la fn

	// Envio de mensaje
	_, err = fmt.Fprintf(c.conn, "[CLIENT %v] Message N°%v\n", c.config.ID, msgID)
	if err != nil {
		log.Errorf("action: send_message | result: fail | client_id: %v | error: %v", c.config.ID, err)
		return false
	}

	// Recibo la respuesta
	responseChan := make(chan string, 1)
	errorChan := make(chan error, 1)

	go func() {
		msg, readErr := bufio.NewReader(c.conn).ReadString('\n')
		if readErr != nil {
			errorChan <- readErr
		} else {
			responseChan <- msg
		}
	}()

	// handles SIGTERM, success, error,timeout
	select {
	case <-signalChan:
		log.Infof("action: SIGTERM_received | result: success | client_id: %v | msg: stopping_gracefully", c.config.ID)
		return false
	case msg := <-responseChan:
		log.Infof("action: receive_message | result: success | client_id: %v | msg: %v", c.config.ID, msg)
		return true
	case err := <-errorChan:
		log.Errorf("action: receive_message | result: fail | client_id: %v | error: %v", c.config.ID, err)
		return false
	case <-time.After(10 * time.Second):
		log.Errorf("action: receive_timeout | result: fail | client_id: %v", c.config.ID)
		return false
	}
}
