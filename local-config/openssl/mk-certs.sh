#
# (C) Copyright IBM Corp. 2020
#
# SPDX-License-Identifier: Apache-2.0
#
# make-certs.sh
# Creates the LinuxForHealth certificates required to enable TLS.
#
PASSWORD=change-password

OPENSSL=`which openssl`
if [ -z "$OPENSSL" ]; then
    echo "Please install openssl."
    exit 1
fi

touch index.txt
echo "01" >> serial.txt

echo "Creating the LinuxForHealth rootCA certificate"
openssl req -nodes -x509 -newkey rsa:4096 -sha256 -days 3650 -keyout rootCA.key \
    -out rootCA.crt -passout pass:$PASSWORD -config ./ca.cnf

echo "Creating a signing request for the LinuxForHealth server certificate"
openssl req -nodes -newkey rsa:2048 -sha256 -out servercert.csr \
    -keyout server.key -subj "/C=US/ST=Texas/L=Austin/O=LinuxForHealth/CN=linuxforhealth.org" \
    -config ./server.cnf

echo "Signing the LinuxForHealth server certificate"
openssl ca -batch -config ca.cnf -policy signing_policy -extensions signing_req -out server.crt \
    -infiles servercert.csr

echo "Creating a signing request for the LinuxForHealth NATS server certificate"
openssl req -nodes -newkey rsa:2048 -sha256 -out natsservercert.csr \
    -keyout nats-server.key -subj "/C=US/ST=Texas/L=Austin/O=LinuxForHealth/CN=linuxforhealth.org" \
    -config ./nats-server.cnf

echo "Signing the LinuxForHealth NATS server certificate"
openssl ca -batch -config ca.cnf -policy signing_policy -extensions signing_req -out nats-server.crt \
    -infiles natsservercert.csr
