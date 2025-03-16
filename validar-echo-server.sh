#!/bin/bash

# Definir variables
SERVER_CONTAINER="server"
SERVER_PORT=12345
TEST_MESSAGE="hello_server"

# Obtener la IP del servidor dentro de la red de Docker
SERVER_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$SERVER_CONTAINER")

# Verificar que se obtuvo la IP correctamente
if [[ -z "$SERVER_IP" ]]; then
    echo "action: test_echo_server | result: fail"
    exit 1
fi

# Enviar mensaje y recibir respuesta con netcat dentro de un contenedor temporal en la misma red
RECEIVED_MESSAGE=$(docker run --rm --network=testing_net busybox nc -w 2 "$SERVER_IP" "$SERVER_PORT" <<< "$TEST_MESSAGE")

# Validar la respuesta
if [[ "$RECEIVED_MESSAGE" == "$TEST_MESSAGE" ]]; then
    echo "action: test_echo_server | result: success"
else
    echo "action: test_echo_server | result: fail"
fi
