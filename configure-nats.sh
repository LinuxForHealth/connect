#!/bin/bash
#
# configure-nats.sh
# Configures the NATS JetStream server.

NATS_SERVICE_NAME=connect_nats-server_1
NATS_CLIENT_PORT=4222
TLSCERT=/conf/lfh-nats-server.pem
TLSKEY=/conf/lfh-nats-server.key
TLSCA=/conf/lfh-root-ca.pem
NKEY=/conf/nats-server.nk

echo "Creating JetStream EVENTS stream"
docker exec -it "${NATS_SERVICE_NAME}" \
              nats --server="${NATS_SERVICE_NAME}":"${NATS_CLIENT_PORT}" \
              --tlscert="${TLSCERT}" \
              --tlskey="${TLSKEY}" \
              --tlsca="${TLSCA}" \
              --nkey="${NKEY}" \
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
              --dupe-window=10s

echo "Creating JetStream push consumer for data synchronization"
docker exec -it "${NATS_SERVICE_NAME}" \
              nats --server="${NATS_SERVICE_NAME}":"${NATS_CLIENT_PORT}" \
              --tlscert="${TLSCERT}" \
              --tlskey="${TLSKEY}" \
              --tlsca="${TLSCA}" \
              --nkey="${NKEY}" \
              con add EVENTS SYNC \
              --ack none \
              --target sync.EVENTS \
              --deliver last \
              --replay instant \
              --filter EVENTS.sync

echo "Creating JetStream pull consumer for data retransmit"
docker exec -it "${NATS_SERVICE_NAME}" \
              nats --server="${NATS_SERVICE_NAME}":"${NATS_CLIENT_PORT}" \
              --tlscert="${TLSCERT}" \
              --tlskey="${TLSKEY}" \
              --tlsca="${TLSCA}" \
              --nkey="${NKEY}" \
              con add EVENTS RESTRANSMIT \
              --pull \
              --ack explicit \
              --deliver all \
              --max-deliver 20 \
              --wait 30s \
              --replay instant \
              --sample 100 \
              --filter EVENTS.retransmit

echo "Creating JetStream ACTIONS stream for workflows"
docker exec -it "${NATS_SERVICE_NAME}" \
              nats --server="${NATS_SERVICE_NAME}":"${NATS_CLIENT_PORT}" \
              --tlscert="${TLSCERT}" \
              --tlskey="${TLSKEY}" \
              --tlsca="${TLSCA}" \
              --nkey="${NKEY}" \
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
              --dupe-window=10s

echo "JetStream EVENTS stream info"
docker exec -it "${NATS_SERVICE_NAME}" \
              nats --server="${NATS_SERVICE_NAME}":"${NATS_CLIENT_PORT}" \
              --tlscert="${TLSCERT}" \
              --tlskey="${TLSKEY}" \
              --tlsca="${TLSCA}" \
              --nkey="${NKEY}" \
              str info EVENTS

echo "JetStream ACTIONS stream info"
docker exec -it "${NATS_SERVICE_NAME}" \
              nats --server="${NATS_SERVICE_NAME}":"${NATS_CLIENT_PORT}" \
              --tlscert="${TLSCERT}" \
              --tlskey="${TLSKEY}" \
              --tlsca="${TLSCA}" \
              --nkey="${NKEY}" \
              str info ACTIONS

echo "NATS JetStream configuration complete"
