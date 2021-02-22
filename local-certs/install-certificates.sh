#!/usr/bin/env sh
# install-certificates.sh
# installs LinuxForHealth locally trusted Root CA and development certificates.
# certificates generated include:
# - Root CA
# - pyConnect development certificate
# - NATS development certificate

SCRIPT_DIRECTORY=$(dirname "$0")

echo "install CA Root certificate"
mkcert -install
echo ""

echo "copying rootCA.pem to $SCRIPT_DIRECTORY"
echo ""
CA_ROOT_LOCATION=$(mkcert -CAROOT)
cp "$CA_ROOT_LOCATION"/rootCA.pem "$SCRIPT_DIRECTORY"

echo "create NATS development certificate"
echo ""
mkcert -cert-file "$SCRIPT_DIRECTORY"/nats-server.pem \
       -key-file "$SCRIPT_DIRECTORY"/nats-server.key \
       nats-server compose_nats-server_1 localhost 127.0.0.1 ::1 \

echo "create LinuxForHealth development certificate"
mkcert -cert-file "$SCRIPT_DIRECTORY"/lfh.pem \
       -key-file "$SCRIPT_DIRECTORY"/lfh.key \
       lfh compose_lfh_1 localhost 127.0.0.1 ::1 \
