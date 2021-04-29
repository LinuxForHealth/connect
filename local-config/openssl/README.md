# LinuxForHealth certificate and store generation

UPDATED: 2/20/21 - The local development environment has been updated to utilize mkcert for local certificate support. The OpenSSL process may be used as an example of how to configure certificates for a non-production deployed environment.

The LinuxForHealth container-support/certs directory contains the scripts required to generate self-signed certs needed for LinuxForHealth. Follow the instructions below to re-generate and install the LinuxForHealth certs.

## Generate the certs, truststore and keystore

Run the following commands to generate and install the LinuxForHealth certs.

```shell script
cd local-config
./clean.sh
./mk-certs.sh
cp *.jks ../../src/main/resources
```

Note: When asked for information for input, just hit return as the defaults have already been provided.

##