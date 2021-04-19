# Local Trusted Certificates

Connect is configured to support secure transmissions (HTTPS/SSL/TLS) for core and external services.
[mkcert](https://github.com/FiloSottile/mkcert)is used to implement secure processing for local/development deployments. Please note that mkcert is not recommended for use in an external deployed environment.
External/deployed environments are expected to utilize valid non-self signed certificates.

Connect uses base-64 encoded "PEM" formatted keys and certificates. Each secured external connection is configured to use a custom SSL context which explicitly defines the keys and certificates used.


## mkcert certificate support

to create certificates
```shell
./local-certs/install-certificates.sh
```

to remove certificates
```shell
./local-certs/uninstall-certificates.sh
```