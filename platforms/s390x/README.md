# Connect on s390x
Most steps to run connect on s390x are the same as described in the main [README](../../README.md), with a few exceptions noted below due to package availability on s390x.

### Required Software
s390x requires the following docker-compose version:

- [Docker Compose 1.25.0 or higher](https://docs.docker.com/compose/install/) for a local container runtime

## Before You Begin
Perform these steps before you get started with the instructions in the main [README](../../README.md).

### Install Packages
To run connect locally (development mode) on s390x you must install librdkafka and additional packages.  If you want to run connect in a docker container, you may skip this step, as the connect container build also installs these packages.  Follow this step to install the required packages:
```shell
sudo apt-get install -y librdkafka-dev
sudo apt-get install -y libxml2-dev
sudo apt-get install -y libxslt1-dev
sudo apt-get install -y python-lxml
```

## Running Connect
Compose 3.7 is supported on Ubuntu 20.04 on s390x (LinuxONE), but LinuxForHealth connect uses compose 3.9 for profile support.  Without compose 3.9 profiles, the easiest way to start connect containers on s390x is to specify the specific containers to start in your docker-compose command line using the instructions below.

### Copy the s390x files
Copy the s390x Dockerfile and docker-compose.yml to the connect directory.
```shell
cd connect
cp platforms/s390x/Dockerfile .
cp platforms/s390x/docker-compose.yml .
```

### Start connect and supporting services
To run connect locally, first start the LinuxForHealth services, then start connect:
```shell
docker-compose up -d nats-server ipfs-node-0 zookeeper kafka ipfs-cluster-0
docker-compose ps
pipenv run connect
```

To run connect in a container, start it with the other LinuxForHealth services:
```shell
docker-compose up -d nats-server ipfs-node-0 zookeeper kafka ipfs-cluster-0 connect
```

### Stop connect and supporting services
Stop the containers as you normally would:
```shell
docker-compose down -v
```
## Working with certificates
Perform this step if you want to create new certificates for connect and connect services. The creation of new certificates is not required, as connect contains a set of default certificates for SSL.

### Install mkcert
Uninstalling existing certificates and creating new certificates requires the mkcert utility, which has been built for you on s390x. To use mkcert, you must place it on your path.  You can leave mkcert in place and add connect/platforms/arm64 to your path, or you can copy connect/platforms/arm64/mkcert to another directory already on your path.

For all other instructions, please refer to the top-level [README](../../README.md) or the [LinuxForHealth documentation](https://linuxforhealth.github.io/docs/).
