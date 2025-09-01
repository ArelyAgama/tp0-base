package common

import (
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// Contains the info about the clients bet
type Bet struct {
	Name		string
	Surname		string
	Document	string
	Birth		string
	Number		string
}

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
	bet    Bet
}

// Creates a Bet from the env variables
func CreateBet() Bet {
	bet := Bet{
		Name: os.Getenv("NOMBRE"),
		Surname: os.Getenv("APELLIDO"),
		Document: os.Getenv("DOCUMENTO"),
		Birth: os.Getenv("NACIMIENTO"),
		Number: os.Getenv("NUMERO"),
	}
	return bet
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig, bet Bet) *Client {
	client := &Client{
		config: config,
		bet:    bet,
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

// StartClientLoop Send bet to the server 
func (c *Client) StartClientLoop() {
	// Channel to receive SIGTERM signal
	signalChan := make(chan os.Signal, 1)
	signal.Notify(signalChan, syscall.SIGTERM)

	// Create the connection to the server
	err := c.createClientSocket()
	if err != nil {
		log.Errorf("action: create_socket | result: fail | client_id: %v | error: %v",
            c.config.ID,
			err,
		)
		return
	} 
	defer func() {
		if c.conn != nil {
			c.conn.Close()
		}
	}()
	
	// Send Bet to the server
	msg := c.serialize()
	err = writeSocket(c.conn, msg)
	if err != nil {
		log.Errorf("action: send_message | result: fail | client_id: %v | error: %v",
            c.config.ID,
			err,
		)
		return
	} 

	// Read Bet ack from server
	bet_msg, err := readSocket(c.conn)
	if err != nil {
		log.Errorf("action: receive_message | result: fail | client_id: %v | error: %v",
            c.config.ID,
			err,
		)
		return
	}
	
	log.Infof("action: receive_message | result: success | client_id: %v | msg: %s",
		c.config.ID,
		bet_msg,
	)

	// Log the required message for EJ5
	log.Infof("action: apuesta_enviada | result: success | dni: %s | numero: %s", 
		c.bet.Document, 
		c.bet.Number,
	)

	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}
