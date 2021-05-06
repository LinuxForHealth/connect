#!/usr/bin/env sh
# install-certificates.sh
# installs LinuxForHealth locally trusted Root CA and development certificates.
# certificates generated include a ROOT CA and certificate/key pairs for:
# - Connect
# - NATS

BASE_DIRECTORY=$(dirname "$0")

echo "install CA Root certificate"
mkcert -install
echo ""

echo "copy root ca to service directories"
CA_ROOT_LOCATION=$(mkcert -CAROOT)

for dir in connect nats
do
  cp "$CA_ROOT_LOCATION"/rootCA.pem "$BASE_DIRECTORY"/"$dir"/lfh-root-ca.pem
done

echo "create NATS development certificate"
echo ""
mkcert -cert-file "$BASE_DIRECTORY"/nats/lfh-nats-server.pem \
       -key-file "$BASE_DIRECTORY"/nats/lfh-nats-server.key \
       nats-server connect_nats-server_1 localhost 127.0.0.1 ::1

echo "create LinuxForHealth development certificate"
echo ""
mkcert -cert-file "$BASE_DIRECTORY"/connect/lfh-connect.pem \
       -key-file "$BASE_DIRECTORY"/connect/lfh-connect.key \
       connect connect_connect_1 localhost 127.0.0.1 ::1

echo "copy self signed service certs to LinuxForHealth connect directory"
echo "Copying NATS ..."
cp "$BASE_DIRECTORY"/nats/lfh-nats-server.pem "$BASE_DIRECTORY"/connect/