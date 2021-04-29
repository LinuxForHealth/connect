#!/usr/bin/env sh
# install-certificates.sh
# installs LinuxForHealth locally trusted Root CA and development certificates.
# certificates generated include:
# - Root CA
# - Connect development certificate
# - NATS development certificate

OUTPUT_DIRECTORY=$(dirname "$0")/certs

echo "install CA Root certificate"
mkcert -install
echo ""

echo "copying rootCA.pem to $OUTPUT_DIRECTORY"
echo ""
CA_ROOT_LOCATION=$(mkcert -CAROOT)
cp "$CA_ROOT_LOCATION"/rootCA.pem "$OUTPUT_DIRECTORY"

echo "create NATS development certificate"
echo ""
mkcert -cert-file "$OUTPUT_DIRECTORY"/nats-server.pem \
       -key-file "$OUTPUT_DIRECTORY"/nats-server.key \
       nats-server connect_nats-server_1 localhost 127.0.0.1 ::1 \

echo "create LinuxForHealth development certificate"
mkcert -cert-file "$OUTPUT_DIRECTORY"/lfh.pem \
       -key-file "$OUTPUT_DIRECTORY"/lfh.key \
       lfh compose_lfh_1 localhost 127.0.0.1 ::1 \
