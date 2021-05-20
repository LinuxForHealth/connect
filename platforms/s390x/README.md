# Connect on s390x
Most steps to run connect on s390x are the same as described in the main [README](../../README.md), with a few exceptions noted below due to package availability on s390x.

## Before You Begin
Perform these steps before you get started with the instructions in the main [README](../../README.md).

### Install mkcert
The mkcert utility has been built for you on s390x, but you need to place it on your path.  You can leave mkcert in place and add connect/platforms/s390x to your path, or you can copy connect/platforms/s390x/mkcert to another directory already on your path. 

### Install librdkafka
To run connect locally (development mode) on s390x you must install librdkafka.  If you want to run connect in a docker container, you may skip this step, as the connect container build also builds librdkafka.  Follow this step to install librdkafka:
```shell
sudo apt-get install -y librdkafka-dev
```

## Running Connect
Compose 3.7 is supported on Ubuntu 20.04 on s390x (LinuxONE), but LinuxForHealth connect uses compose 3.9 for profile support.  Without compose 3.9 profiles, the easiest way to start connect containers on s390x is to specify the specific containers to start in your docker-compose command line using the instructions below.

### Start connect and supporting services
To run connect locally, first start the LinuxForHealth services, then start connect:
```shell
cd connect/platforms/s390x
docker-compose up -d nats-server zookeeper kafka ibm-fhir
docker-compose ps
pipenv run connect
```

To run connect in a container, start it with the other LinuxForHealth services:
```shell
cd connect/platforms/s390x
docker-compose up -d connect nats-server zookeeper kafka ibm-fhir
```

### Stop connect and supporting services
Stop the containers as you normally would:
```shell
cd connect/platforms/s390x
docker-compose down -v
```

For any other instructions, please refer to the top-level [README](../../README.md) or the [LinuxForHealth documentation](https://linuxforhealth.github.io/docs/).
