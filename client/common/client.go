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
	// Channel simple para recibir SIGTERM
	signalChan := make(chan os.Signal, 1)
	signal.Notify(signalChan, syscall.SIGTERM)

	// Loop principal con mensajes
	for msgID := 1; msgID <= c.config.LoopAmount; msgID++ {
		// Verificar SIGTERM antes de cada mensaje
		select {
			case <-signalChan:
				log.Infof("action: SIGTERM_detected | result: success | client_id: %v", c.config.ID)
				return
			default:
				// Continúa normal
		}

		// Crear conexión para este mensaje
		err := c.createClientSocket()
		if err != nil {
			log.Errorf("action: create_socket | result: fail | client_id: %v | error: %v", c.config.ID, err)
			return
		}

		// Enviar mensaje
		_, err = fmt.Fprintf(c.conn, "[CLIENT %v] Message N°%v\n", c.config.ID, msgID)
		if err != nil {
			log.Errorf("action: send_message | result: fail | client_id: %v | error: %v", c.config.ID, err)
			c.conn.Close()
			return
		}

		// Recibir respuesta (blocking, simple)
		msg, err := bufio.NewReader(c.conn).ReadString('\n')
		c.conn.Close()

		if err != nil {
			log.Errorf("action: receive_message | result: fail | client_id: %v | error: %v", c.config.ID, err)
			return
		}

		log.Infof("action: receive_message | result: success | client_id: %v | msg: %v", c.config.ID, msg)

		// Esperar antes del siguiente mensaje
		time.Sleep(c.config.LoopPeriod)
	}

	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}
