# Local Configuration

This project directory contains configuration tooling to support running connect, and it's dependent services locally. Contents include:

* install-certificates.sh - a shell script used to generate local self-signed certificates.
* uninstall-certificates.sh - a shell script used to remove local self-signed certificates from the system.
* certs - directory where local self-signed certificates are generated.
* nats - contains NATS configuration files
* openssl - "archived" directory which provides examples and documentation for generating pki for deployed environments.


## Local Trusted Certificates

Connect is configured to support secure transmissions (HTTPS/SSL/TLS) for core and external services.
[mkcert](https://github.com/FiloSottile/mkcert)is used to implement secure processing for local/development deployments. Please note that mkcert is not recommended for use in an external deployed environment.
External/deployed environments are expected to utilize valid non-self signed certificates.

Connect uses base-64 encoded "PEM" formatted keys and certificates. Each secured external connection is configured to use a custom SSL context which explicitly defines the keys and certificates used.


### mkcert certificate support

#### Create certificates
```shell
./local-config/install-certificates.sh
```

#### Remove certificates
```shell
./local-config/uninstall-certificates.sh
```

Certificates are generated in the [certs directory](./certs).