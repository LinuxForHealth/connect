# LinuxForHealth certificate and store generation

The LinuxForHealth container-support/certs directory contains the scripts required to generate self-signed certs needed for LinuxForHealth. Follow the instructions below to re-generate and install the LinuxForHealth certs.

## Generate the certs, truststore and keystore

Run the following commands to generate and install the LinuxForHealth certs.

```shell script
cd local-certs
./clean.sh
./mk-certs.sh
cp *.jks ../../src/main/resources
```

Note: When asked for information for input, just hit return as the defaults have already been provided.

##