# Local Trusted Certificates

pyConnect is configured to support secure transmissions (HTTPS/SSL/TLS) for core and external services.
[mkcert](https://github.com/FiloSottile/mkcert)is used to implement secure processing for local/development deployments. Please note that mkcert is not recommended for use in an external deployed environment.
External/deployed environments are expected to utilize valid non-self signed certificates.


## mkcert certificate support

to create certificates
```shell
./local-certs/install-certificates.sh
```

to remove certificates
```shell
./local-certs/uninstall-certificates.sh
```