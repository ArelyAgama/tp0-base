package common

import (
	"encoding/csv"
	"fmt"
	"io"
	"net"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// Info de la apuesta
type Bet struct {
	Name     string
	Surname  string
	Document string
	Birth    string
	Number   string
}

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
	BatchSize     int // Cantidad de apuestas por batch
}

type Client struct {
	config ClientConfig
	conn   net.Conn
	bet    Bet
}

// Creo la apuesta desde las variables de entorno
func CreateBet() Bet {
	bet := Bet{
		Name:     os.Getenv("NOMBRE"),
		Surname:  os.Getenv("APELLIDO"),
		Document: os.Getenv("DOCUMENTO"),
		Birth:    os.Getenv("NACIMIENTO"),
		Number:   os.Getenv("NUMERO"),
	}
	return bet
}

// ReadBetBatch lee un batch de apuestas desde un CSV reader
func (c *Client) ReadBetBatch(reader *csv.Reader) ([]Bet, error) {
	var batch []Bet

	for len(batch) < c.config.BatchSize { // Mientras el tamaño del batch sea menor al tamaño configurado
		record, err := reader.Read()

		// Si se alcanza el final del archivo, se sale del bucle
		if err == io.EOF {
			break
		}
		if err != nil {
			return nil, fmt.Errorf("error reading CSV: %w", err)
		}

		// Validar formato CSV: Nombre,Apellido,Documento,Fecha,Numero
		if len(record) != 5 {
			return nil, fmt.Errorf("invalid CSV record: expected 5 fields, got %d", len(record))
		}

		bet := Bet{
			Name:     record[0],
			Surname:  record[1],
			Document: record[2],
			Birth:    record[3],
			Number:   record[4],
		}

		batch = append(batch, bet)
	}

	return batch, nil
}

// SerializeBatch convierte un batch de apuestas al formato del protocolo
func (c *Client) SerializeBatch(batch []Bet, isLastBatch bool) string {
	var lines []string

	// Primera línea: cantidad de apuestas + EOF marker si es el último
	if isLastBatch {
		lines = append(lines, fmt.Sprintf("%d|EOF", len(batch)))
	} else {
		lines = append(lines, fmt.Sprintf("%d", len(batch)))
	}

	// Agregar cada apuesta
	//bet = {Name: "María", Surname: "López", Document: "23456", Birth: "1991-02-02", Number: "43"}
	//line = "agency_1/María/López/23456/1991-02-02/43"
	//lines = ["agency_1/Juan/Pérez/12345/1990-01-01/42",
	//     "agency_1/María/López/23456/1991-02-02/43"]

	for _, bet := range batch {
		line := fmt.Sprintf("%s/%s/%s/%s/%s/%s",
			c.config.ID, bet.Name, bet.Surname, bet.Document, bet.Birth, bet.Number)
		lines = append(lines, line)
	}

	return strings.Join(lines, "\n")
}

// Agrego la apuesta como parametro del cliente
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

// StartClientLoop procesa el archivo CSV por batches y los envía al servidor
func (c *Client) StartClientLoop() {
	// Channel to receive SIGTERM signal
	signalChan := make(chan os.Signal, 1)
	signal.Notify(signalChan, syscall.SIGTERM)

	// Crear conexión con el servidor
	if err := c.createClientSocket(); err != nil {
		log.Errorf("Failed to connect to server: %v", err)
		return
	}
	defer c.conn.Close()

	// Verificar SIGTERM antes de empezar
	select {
	case <-signalChan:
		log.Infof("action: SIGTERM_detected | result: success | client_id: %v", c.config.ID)
		return
	default:
		// Continúa normal
	}

	// Crear conexion para el cliente
	err := c.createClientSocket()
	if err != nil {
		log.Errorf("action: create_socket | result: fail | client_id: %v | error: %v",
			c.config.ID, err)
		return
	}
	defer func() {
		if c.conn != nil {
			c.conn.Close()
		}
	}()

	// Abrir archivo CSV desde variable de entorno o construir path por defecto
	filename := os.Getenv("CLI_CSV_FILE")
	if filename == "" {
		filename = fmt.Sprintf(".data/agency-%s.csv", c.config.ID)
	}

	file, err := os.Open(filename)
	if err != nil {
		log.Errorf("action: open_file | result: fail | client_id: %v | file: %s | error: %v",
			c.config.ID, filename, err)
		return
	}
	defer file.Close()

	reader := csv.NewReader(file)
	batchCount := 0
	totalBets := 0

	// Procesar archivo por batches
	for {
		batch, err := c.ReadBetBatch(reader)
		if err != nil {
			log.Errorf("action: read_batch | result: fail | client_id: %v | error: %v",
				c.config.ID, err)
			return
		}

		if len(batch) == 0 {
			break // No hay más datos
		}

		batchCount++
		totalBets += len(batch)

		// Determinar si es el último batch
		isLastBatch := len(batch) < c.config.BatchSize

		// Serializar batch
		message := c.SerializeBatch(batch, isLastBatch)

		// Enviar batch
		err = writeSocket(c.conn, message)
		if err != nil {
			log.Errorf("action: send_batch | result: fail | client_id: %v | batch: %d | error: %v",
				c.config.ID, batchCount, err)
			return
		}

		// Recibir ACK del servidor
		ackMsg, err := readSocket(c.conn)
		if err != nil {
			log.Errorf("action: receive_ack | result: fail | client_id: %v | batch: %d | error: %v",
				c.config.ID, batchCount, err)
			return
		}

		log.Infof("action: batch_processed | result: success | client_id: %v | batch: %d | size: %d | ack: %s",
			c.config.ID, batchCount, len(batch), ackMsg)

		if isLastBatch {
			break
		}
	}

	log.Infof("action: all_batches_sent | result: success | client_id: %v | total_batches: %d | total_bets: %d",
		c.config.ID, batchCount, totalBets)
}
