# pyConnect
LinuxForHealth Connectors for Inbound Data Processing

## Getting Started

### Required Software
The LinuxForHealth pyConnect development environment requires the following:

- [git](https://git-scm.com) for project version control
- [mkcert](https://github.com/FiloSottile/mkcert) for https support
- [Python 3.8 or higher](python download for mac) for runtime/coding support
- [Docker Compose](https://docs.docker.com/compose/install/) for a local container runtime

### Getting Started
Clone the project and navigate to the root directory
```shell
git clone https://github.com/LinuxForHealth/pyconnect
cd pyconnect
```

Create a virtual environment
```shell
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

Install pyconnect with dev and test dependencies
```shell
pip install -e .[dev,test]
# note if using zsh shell the extra dependencies require quoting
# pip install -e ".[dev,test]"
```

Generate local certs for NATS Jetstream and pyConnect
```shell
cd local-certs
./mk-certs.sh
# hit enter to accept defaults from cnf files
cd ../
```

Start supporting services and pyconnect
```shell
docker-compose up -d
docker-compose ps
UVICORN_CERT=./local-certs/server.crt UVICORN_CERT_KEY=./local-certs/server.key UVICORN_RELOAD=True python pyconnect/main.py 
```

Browse to `https://localhost:5000/docs` to view the Open API documentation
Please note that the browser may prompt to trust the certificate as it is self-signed.

### Docker Image
The pyconnect docker image is an "incubating" feature. The image builds successfully but additional work is required to
integrate certificates and supporting components such as NATS Jetstream, Kafka, etc. 

Build the image
```shell
docker build -t linuxforhealth/pyconnect:0.25.0 .
```

The command to launch the container will be similar to
```shell
docker run --name pyconnect -d \
  -v local-certs:/home/lfh/certs:ro \
  -e UVICORN_CERT=./home/lfh/certs/server.crt \
  -e UVICORN_CERT_KEY=./home/lfh/certs/server.key \
  linuxforhealth/pyconnect:0.25.0
```
