# fabric-client
fabric-client is a Node.js Hyperledger Fabric blockchain client that allows transactions to be sent to the blockchain via a REST API or a NATS listener.  The fabric-client works with the fhir-data smart contract to provide storage of FHIR resources in the blockchain.

## Pre-requisites
If you don't have a Hyperledger Fabric instance and would like to install the Hyperledger Fabric test-network on your local machine, you can follow the "Test with test-network" instructions below.

## Install the contract
This repo contains fhir-data@1.0.0.tar.gz which is a Hyperledger Fabric Typescript contract that stores FHIR-R4 records in the blockchain and performs eligibility verification checks.  Install this contract in your Hyperledger Fabric network, or follow the instructions below to install it in a test-network instance.

## Test with test-network
The fabric client can be tested using a local Hyperledger Fabric test-network instance.  Follow the steps below to set up test-network on your local machine.

### Install Hyperledger fabric-samples
Follow the [instructions](https://hyperledger-fabric.readthedocs.io/en/latest/getting_started.html) to install the Hyperledger Fabric samples repository and pre-requisites.

### Start the test-network
```shell
cd fabric-samples/test-network
./network.sh up createChannel -c channel1 -ca
```

### Copy the contract and install script to the test-network
Copy the contract and install script to the test-network directory.  The contract will be installed in later step.
```shell
cp <connect-path>/connect/local-config/fabric/fhir-data@1.0.0.tar.gz .
cp <connect-path>/connect/local-config/fabric/install_contract.sh .
```

### Add the peer binaries to your path
```shell
export PATH=${PWD}/../bin:$PATH
export FABRIC_CFG_PATH=$PWD/../config/
```

### Install the contract
```shell
./install_contract.sh
```

At the end of this step, you should see:
```shell
Committed chaincode definition for chaincode 'fhir-data' on channel 'channel1':
Version: 1.0, Sequence: 1, Endorsement Plugin: escc, Validation Plugin: vscc, Approvals: [Org1MSP: true, Org2MSP: true]
```

### Generate the connection json file
Generate the test-network connection-full.json file, which describes the fabric network you just deployed.  To do that, first edit connect/local-config/fabric/conf/ccp-generate.sh and set TESTNET_PATH to your test-network directory. Then generate connection-full.json:
```shell
cd connect/local-config/fabric/conf
./ccp-generate.sh
```
Note:  If you have redeployed test-network, delete all the .id files under connect/local-config/fabric/conf/wallet, as these will no longer work with your new test-network deployment.  They will be regenerated when the connect fabric client starts.

## Configure LinuxForHealth connect
Configure LinuxForHealth connect to use the test-network Docker network.  This is required for contract network connectivity with the connect NATS server.  Change the network name in connect/docker-compose.yml to `fabric_test`:
```shell
networks:
  main:
    name: fabric_test
```

## Configure the fabric client
Copy your connection json file for your Hyperledger Fabric to connect/local-config/fabric/conf and specify the filename in connect/local-config/fabric/conf.  If you generated connection-full.json in the previous step, there is nothing to do for this step.

You can further edit the fabric-client config.json in connect/local-config/fabric/conf and adjust the settings for your fabric, but you should be able to use the configuration with test-network without changes.  Please see the table below if you do need to make changes:

| Setting | Example | Description |
| ------- | ------- | ----------- |
| channel | channel1 | The channel on which your Hyperledger Fabric contract is deployed. |
| contract | fhir-data | The name of the deployed contract. |
| port | 9043 | The port on which the fabric client listens for incoming REST API calls. |
| connection_profile | conf/connection-full.json | The location of the Hyperledger Fabric connection profile. |
| wallet_location | conf/wallet | The location of the Hyperledger Fabric wallet directory. 
| use_discovery | false | Whether to use the fabric-network API's discovery service.  Use `true` if your Hyperledger Fabric servers are DNS discoverable, otherwise use `false`. |
| as_local_host | false | If your Hyperledger Fabric servers are running locally and `use_discovery` is `true`, use `true`, otherwise use `false`. |
| use_nats | true | Whether to use NATS to receive messages from LinuxForHealth.  This should always be true when using LinuxForHealth. |
| nats_servers | ["nats-server:4222"] | An array of NATS servers from which the fabric client will receive messages. |
| nats_nkey | conf/certs/nats-server.nk | The NATS nkey private key that the client needs to connect to the LinuxForHealth NATS server. |
| nats_ca_file | ./conf/certs/lfh-root-ca.pem | The CA file to use when connecting to the LinuxForHealth NATS server. |
| enroll_admin | true | When using test-network, whether to enroll the admin.  In general this will be true, at least initially when using test-network.  Once the id is in the local wallet, you can leave it set to true or change it to false. |
| admin_name | admin | The name of the admin to enroll when `enroll_admin` is `true`. |
| admin_pw | adminpw | The password of the admin to enroll when `enroll_admin` is `true`. |
| register_user | true | When using test-network, whether to enroll a user.  In general this will be true, at least initially when using test-network.  Once the id is in the local wallet, you can leave it set to true or change it to false. |
| user_name | admin | The name of the user to register when `register_user` is `true`. |
| certificate_authority | ca.org1.example.com | The name of the Hyperledger Fabric CA to specify when `register_user` is `true`. |
| msp_id | Org1MSP | The name of the Hyperledger Fabric Membership Service Provider to use when  `register_user` is `true`. |

## Start the client
Use the docker-compose fabric profile to start the fabric client with the rest of the LFH services:
```shell
docker-compose --profile deployment --profile fabric up -d
```

## Configure NATS JetStream
The Hyperledger Fabric contract uses NATS JetStream to publish to a stream, so configure JetStream in LinuxForHealth connect.
```shell
./configure-nats.sh
```

That's it - you're ready to send transactions to LinuxForHealth and store them in your blockchain!
