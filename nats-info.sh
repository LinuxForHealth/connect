#!/bin/bash
#
# nats-info.sh
# Provides NATS JetStream stream info.

NATS_SERVICE_NAME=connect_nats-server_1
NATS_CLIENT_PORT=4222
TLSCERT=/conf/lfh-nats-server.pem
TLSKEY=/conf/lfh-nats-server.key
TLSCA=/conf/lfh-root-ca.pem
NKEY=/conf/nats-server.nk

echo "JetStream EVENTS stream info"
echo "****************************"
docker exec -it "${NATS_SERVICE_NAME}" \
              nats --server="${NATS_SERVICE_NAME}":"${NATS_CLIENT_PORT}" \
              --tlscert="${TLSCERT}" \
              --tlskey="${TLSKEY}" \
              --tlsca="${TLSCA}" \
              --nkey="${NKEY}" \
              str info EVENTS

echo "JetStream EVENTS stream SYNC consumer info"
echo "******************************************"
docker exec -it "${NATS_SERVICE_NAME}" \
              nats --server="${NATS_SERVICE_NAME}":"${NATS_CLIENT_PORT}" \
              --tlscert="${TLSCERT}" \
              --tlskey="${TLSKEY}" \
              --tlsca="${TLSCA}" \
              --nkey="${NKEY}" \
              consumer info EVENTS SYNC
