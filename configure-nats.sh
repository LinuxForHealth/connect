#!/bin/bash
#
# (C) Copyright IBM Corp. 2020
# SPDX-License-Identifier: Apache-2.0
#
# configure-nats.sh
# Configures the NATS JetStream server.

# wait parameters used to determine when the services within a container are available
SLEEP_INTERVAL=2
MAX_CHECKS=10

NATS_SERVICE_NAME=pyconnect_nats-server_1
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
              --target EVENTS.* \
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

echo "Creating JetStream consumer for ACTIONS.persist"
docker exec -it "${NATS_SERVICE_NAME}" \
              nats --server="${NATS_SERVICE_NAME}":"${NATS_CLIENT_PORT}" \
              --tlscert="${TLSCERT}" \
              --tlskey="${TLSKEY}" \
              --tlsca="${TLSCA}" \
              con add ACTIONS SUBSCRIBER \
              --ack none \
              --target ACTIONS.persist \
              --deliver last \
              --replay instant \
              --filter '' > /dev/null

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
