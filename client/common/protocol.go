package common

import (
	"net"
	"strconv"
)

const (
	HEADER_LENGTH = 4
    READ_BUF_SIZE  = 1024
    WRITE_BUF_SIZE = 1024
)

// 
func getHeader(msg string) string {
	msg_len := strconv.Itoa(len(msg)) // len("AGENCY/NOMBRE/APELLIDO/DOCUMENTO/NACIMIENTO/NUMERO") => "51"
	msg_len_bytes := len(msg_len) // len("51") => 2
	for i := 0; i < HEADER_LENGTH - msg_len_bytes; i++ {
		msg_len = "0" + msg_len
	}
	return msg_len // "0051"
}

// Escribo el mensaje en el socket con el header correspondiente
func writeSocket(conn net.Conn, msg string) error {
	// Header
	header := getHeader(msg) // "0051" bytes
	complete_msg := header + msg

	err := handleShortWrite(conn, complete_msg, len(complete_msg))
	if err != nil {
		return err
	}
	return nil
}

// Aseguro que se escriba todo el mensaje
func handleShortWrite(conn net.Conn, msg string, total_bytes_to_write int) error {
	bytes_wrote := 0
	for bytes_wrote< total_bytes_to_write { // bytes_to_write = 55
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

// Aseguro que se lea todo el mensaje
func handleShortRead(conn net.Conn, total_bytes_to_read int) (string, error) {
	bytes_read := 0
	msg := ""
	for bytes_read < total_bytes_to_read {
		buf := make([]byte, total_bytes_to_read - bytes_read)
		nbytes, err := conn.Read(buf)
		if err != nil {
			return "", err
		}
		msg += string(buf[:nbytes])
		bytes_read += nbytes
	}
	return msg, nil
}

