#!/bin/bash
#
# configure-nats.sh
# Configures the NATS JetStream server.

NATS_SERVICE_NAME=connect_nats-server_1
NATS_CLIENT_PORT=4222
TLSCERT=/certs/nats-server.pem
TLSKEY=/certs/nats-server.key
TLSCA=/certs/rootCA.pem

echo "Creating JetStream EVENTS stream for data synchronization"
docker exec -it "${NATS_SERVICE_NAME}" \
              nats --server="${NATS_SERVICE_NAME}":"${NATS_CLIENT_PORT}" \
              --tlscert="${TLSCERT}" \
              --tlskey="${TLSKEY}" \
              --tlsca="${TLSCA}" \
              str add EVENTS \
              --subjects EVENTS.* \
              --ack \
              --max-msgs=-1 \
              --max-bytes=-1 \
              --max-age=1y \
              --storage file \
              --retention limits \
              --max-msg-size=-1 \
              --discard old \
              --dupe-window=10s > /dev/null

echo "Creating JetStream consumer for data synchronization"
docker exec -it "${NATS_SERVICE_NAME}" \
              nats --server="${NATS_SERVICE_NAME}":"${NATS_CLIENT_PORT}" \
              --tlscert="${TLSCERT}" \
              --tlskey="${TLSKEY}" \
              --tlsca="${TLSCA}" \
              con add EVENTS SUBSCRIBER \
              --ack none \
              --target EVENTS.sync \
              --deliver last \
              --replay instant \
              --filter '' > /dev/null

echo "Creating JetStream ACTIONS stream for workflows"
docker exec -it "${NATS_SERVICE_NAME}" \
              nats --server="${NATS_SERVICE_NAME}":"${NATS_CLIENT_PORT}" \
              --tlscert="${TLSCERT}" \
              --tlskey="${TLSKEY}" \
              --tlsca="${TLSCA}" \
              str add ACTIONS \
              --subjects ACTIONS.* \
              --ack \
              --max-msgs=-1 \
              --max-bytes=-1 \
              --max-age=1y \
              --storage file \
              --retention limits \
              --max-msg-size=-1 \
              --discard old \
              --dupe-window=10s > /dev/null

echo "JetStream EVENTS stream info"
docker exec -it "${NATS_SERVICE_NAME}" \
              nats --server="${NATS_SERVICE_NAME}":"${NATS_CLIENT_PORT}" \
              --tlscert="${TLSCERT}" \
              --tlskey="${TLSKEY}" \
              --tlsca="${TLSCA}" \
              str info EVENTS

echo "JetStream ACTIONS stream info"
docker exec -it "${NATS_SERVICE_NAME}" \
              nats --server="${NATS_SERVICE_NAME}":"${NATS_CLIENT_PORT}" \
              --tlscert="${TLSCERT}" \
              --tlskey="${TLSKEY}" \
              --tlsca="${TLSCA}" \
              str info ACTIONS

echo "NATS JetStream configuration complete"
