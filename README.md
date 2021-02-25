# pyConnect
LinuxForHealth Connectors for Inbound Data Processing

## Getting Started

### Required Software
The LinuxForHealth pyConnect development environment requires the following:

- [git](https://git-scm.com) for project version control
- [mkcert](https://github.com/FiloSottile/mkcert) for local trusted certificates
- [Python 3.8 or higher](https://www.python.org/downloads/mac-osx/) for runtime/coding support
- [Docker Compose](https://docs.docker.com/compose/install/) for a local container runtime

For Windows 10 users, we suggest using [Windows Subsystem for Linux](https://docs.microsoft.com/en-us/windows/wsl/install-win10)

### Getting Started
#### Clone the project and navigate to the root directory
```shell
git clone https://github.com/LinuxForHealth/pyconnect
cd pyconnect
```

#### Create a virtual environment
```shell
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

#### Install pyconnect with dev and test dependencies
```shell
pip install -e .[dev,test]
# note if using zsh shell the extra dependencies require quoting
# pip install -e ".[dev,test]"
```

#### Generate trusted local certs for pyConnect and supporting services

```shell
./local-certs/install-certificates.sh
```
For more information on pyConnect and HTTPS/TLS support, please refer to [the local cert readme](./local-certs/README.md).

#### Create Swarm Key for a private IPFS peer network
```shell
docker run --rm golang:1.9 sh -c 'go get github.com/Kubuxu/go-ipfs-swarm-key-gen/ipfs-swarm-key-gen && ipfs-swarm-key-gen'
/key/swarm/psk/1.0.0/
/base16/
f744ccf21ef090407977a33e01deb0a0c6a3397ae0366ff6f3c749e200f2510d
```
Persist the generated output (example above) to `./private-ipfs-network/.ipfs/swarm.key`

#### Create IPFS Cluster Secret (32-bit hex-encoded string) and update `CLUSTER_SECRET` in `docker-compose.yml`
```shell
openssl rand -hex 32
```

#### Start supporting services and pyconnect
- To start services without IPFS support, please use the `dev` profile.
- To add IPFS support use the `ipfs` profile.
```shell
docker-compose --profile dev up -d
docker-compose ps
PYCONNECT_CERT=./local-certs/lfh.pem \
  PYCONNECT_CERT_KEY=./local-certs/lfh.key \
  UVICORN_RELOAD=True \
  python pyconnect/main.py 
```

#### Configure NATS streams and consumers
After starting the containers, configure NATS JetStream streams and consumers.
```shell
./configure-nats.sh
```

Browse to `https://localhost:5000/docs` to view the Open API documentation

### Docker Image
The pyconnect docker image is an "incubating" feature. The image builds successfully but additional work is required to
integrate certificates and supporting components such as NATS Jetstream, Kafka, etc. 

#### Build the image
```shell
docker build -t linuxforhealth/pyconnect:0.25.0 .
```
