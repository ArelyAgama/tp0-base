# Config
SERVER_NAME="server"
SERVER_PORT="12345"
NETWORK_NAME="tp0_testing_net"
TEST_MESSAGE="Hello Echo Server"

# Enviar mensaje al servidor usando netcat en un contenedor
RESPONSE=$(docker run --rm --network "$NETWORK_NAME" busybox sh -c "echo '$TEST_MESSAGE' | nc $SERVER_NAME $SERVER_PORT")

if [ "$RESPONSE" = "$TEST_MESSAGE" ]; then
    echo "action: test_echo_server | result: success"
else
    echo "action: test_echo_server | result: fail"
fi
