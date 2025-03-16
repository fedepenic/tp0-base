#!/bin/sh

# Configuración
CONTAINER_NAME="tp0_echo_server"  # Nombre del contenedor del servidor
NETWORK_NAME="tp0_testing_net"   # Nombre de la red de Docker
SERVER_HOST="server"             # Nombre del servidor en la red de Docker
PORT=12345                       # Puerto del servidor
MESSAGE="Hello, Echo Server"      # Mensaje de prueba

# Verificar si la red de Docker existe
if ! docker network ls | grep -q "$NETWORK_NAME"; then
    echo "Docker network $NETWORK_NAME not found"
    echo "action: test_echo_server | result: fail"
    exit 1
fi

# Ejecutar Netcat dentro de un contenedor temporal en la misma red
RESPONSE=$(docker run --rm --network "$NETWORK_NAME" busybox sh -c \
    "(echo '$MESSAGE'; sleep 1) | nc $SERVER_HOST $PORT")

# Verificar si la respuesta es la esperada (uso de `[ ... ]` en lugar de `[[ ... ]]`)
if [ "$RESPONSE" = "$MESSAGE" ]; then
    echo "action: test_echo_server | result: success"
else
    echo "action: test_echo_server | result: fail"
fi
