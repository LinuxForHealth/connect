# Local Configuration

This project directory contains configuration tooling to support running connect, and it's dependent services locally for development use. Contents include:

* install-certificates.sh - a shell script used to generate a locally trusted Root CA and self-signed certificates.
* uninstall-certificates.sh - a shell script used to remove generated certificates.
* connect - contains Connect configuration files and certificates
* nats - contains NATS configuration files and certificates
* openssl - "archived" directory which provides examples and documentation for generating pki for deployed environments.
* ipfs - IPFS cluster and node configuration, including volume mount points

## Local Trusted Certificates

Connect is configured to support secure transmissions (HTTPS/SSL/TLS) for core and external services.
[mkcert](https://github.com/FiloSottile/mkcert)is used to implement secure processing for local/development deployments. Please note that mkcert is not recommended for production use.
External/deployed environments are expected to utilize valid non-self signed certificates.  Please see instructions for using mkcert on [s390x](./platforms/s390x/README.md) and [arm64](./platforms/arm64/README.md) before creating new certificates on these platforms.

Connect uses base-64 encoded "PEM" formatted keys and certificates. Each secured external connection is configured to use a custom SSL context. The context is configured using the `CONNECT_CA_FILE` and `CONNECT_CA_PATH` environment variables.


### mkcert certificate support

#### Create certificates
```shell
./local-config/install-certificates.sh
```

#### Remove certificates
```shell
./local-config/uninstall-certificates.sh
```
