package common

import (
	"net"
	"fmt"
	"strconv"
	"reflect"
	"strings"
)

const (
    READ_BUF_SIZE  = 1024
    WRITE_BUF_SIZE = 1024
	HEADER_LENGTH = 4
)

// Called by writeSocket(). It returns the protocols header for a message.
func getHeader(msg string) string {
	msg_len := strconv.Itoa(len(msg))
	msg_len_bytes := len(msg_len)
	for i := 0; i < HEADER_LENGTH - msg_len_bytes; i++ {
		msg_len = "0" + msg_len
	}
	return msg_len
}

// Writes the message into the received socket
func writeSocket(conn net.Conn, msg string) error {
	// Add header
	header := getHeader(msg)
	complete_msg := header + msg

	err := handleShortWrite(conn, complete_msg, len(complete_msg))
	if err != nil {
		return err
	}
	return nil
}

// Called by writeSocket(). It makes sure that if a short-write happens,
// the rest of the message is also sent.
func handleShortWrite(conn net.Conn, msg string, bytes_to_write int) error {
	// Send serialized message to server, handling short write
	bytes_wrote := 0
	for bytes_wrote < bytes_to_write {
		nbytes, err := conn.Write([]byte(msg[bytes_wrote:]))
		if err != nil {
			return err
		}
		bytes_wrote += nbytes
	}

	return nil
}

// Reads from the received socket.
// It returns the message received or the error.
func readSocket(conn net.Conn) (string, error) {
	// Read header
	header, err := handleShortRead(conn, HEADER_LENGTH)
	if err != nil {
		return header, err
	}

	// Read message
	msg_len, _ := strconv.Atoi(header)
	msg, err := handleShortRead(conn, msg_len)
	
	return msg, err
}

// Called by readSocket(). It makes sure that if a short-read happens,
// the rest of the message is also read.
func handleShortRead(conn net.Conn, bytes_to_read int) (string, error) {
	bytes_read := 0
	msg := ""
	for bytes_read < bytes_to_read {
		buf := make([]byte, bytes_to_read - bytes_read)
		nbytes, err := conn.Read(buf)
		if err != nil {
			return "", err
		}
		msg += string(buf[:nbytes])
		bytes_read += nbytes
	}
	return msg, nil
}

// Serializes the clients bet into a string by iterating over the Bet fields
func (c *Client) serialize() string {
	msg := c.config.ID + "/"
	v := reflect.ValueOf(c.bet)

	for i := 0; i < v.NumField(); i++ {
		val := v.Field(i).Interface()
		msg += fmt.Sprintf("%s/", val)
	}

	msg = strings.TrimSuffix(msg, "/")

	return msg
}
