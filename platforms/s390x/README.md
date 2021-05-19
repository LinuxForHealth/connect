# Connect on s390x
Most steps to run connect on s390x are the same as described in the main [README](../../README.md), with a few exceptions noted below.

## Before You Begin
Perform these steps before you get started with the instructions in the main [README](../../README.md).

### Install mkcert
The mkcert utility has been built for you on s390x, but you need to place it on your path.  You can leave mkcert in place and add connect/platforms/s390x to your path, or you can copy connect/platforms/s390x/mkcert to another directory already on your path. 

### Install librdkafka
To run connect locally (development mode) you must install librdkafka.  If you want to run connect in a docker container, you may skip this step.  Follow this step to install librdkafka:
```shell
sudo apt-get install -y librdkafka-dev
```

## Running Connect
Use these instructions to start and stop LinuxForHealth connect on s390x.

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
