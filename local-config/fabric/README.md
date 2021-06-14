# fabric-client
fabric-client is a Node.js Hyperledger Fabric blockchain client that allows transactions to be sent to the blockchain via a REST API or a NATS listener.  The fabric-client works with the fhir-data smart contract to provide storage of FHIR patient resources in the blockchain.

## Pre-requisites
If you don't have a Hyperledger Fabric instance and would like to install the Hyperledger Fabric test-network on your local machine, you can follow the "testing with test-network" instructions below.

## Install the contract
This repo contains fhir-data.tar.gz which is a Hyperledger Fabric Typescript contract for storing FHIR-R4 Patient records in the blockchain.  Install this contract in your Hyperledger Fabric network, or follow the instructions below to install it in a test-network instance.

## Test with test-network
The fabric client can be tested using a local Hyperledger Fabric test-network instance.  Follow the steps below to set up test-network on your local machine.

### Install Hyperledger fabric-samples
Follow the [instructions](https://hyperledger-fabric.readthedocs.io/en/latest/getting_started.html) to install the Hyperledger Fabric samples repository and pre-requisites.

### Start the test-network
```shell
cd fabric-samples/test-network
./network.sh up createChannel -c channel1 -ca
```

### Copy the contract to the test-network
Copy the contract to the test-network directory.  It will be installed in later step.
```shell
cp <fabric-client-path>/fabric-client/fhir-data.tar.gz .
```

### Install the contract

#### Install the contract (chaincode) as Org1.
```shell
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=localhost:7051
peer lifecycle chaincode install fhir-data.tar.gz
```
You should see a result like:
```shell
2021-06-01 15:49:26.260 CDT [cli.lifecycle.chaincode] submitInstallProposal -> INFO 001 Installed remotely: response:<status:200 payload:"\nNfhir-data_1.0:b2f0f237531073839bafbe0bf1fa324c163f1b3364ad4762b8dd878ba59184c4\022\rfhir-data_1.0" > 
2021-06-01 15:49:26.262 CDT [cli.lifecycle.chaincode] submitInstallProposal -> INFO 002 Chaincode code package identifier: fhir-data_1.0:b2f0f237531073839bafbe0bf1fa324c163f1b3364ad4762b8dd878ba59184c4
```

#### Install the contract as Org2.
```shell
export CORE_PEER_LOCALMSPID="Org2MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org2.example.com/users/Admin@org2.example.com/msp
export CORE_PEER_ADDRESS=localhost:9051
peer lifecycle chaincode install fhir-data.tar.gz
```
You should see a result like:
```shell
2021-06-01 15:52:15.817 CDT [cli.lifecycle.chaincode] submitInstallProposal -> INFO 001 Installed remotely: response:<status:200 payload:"\nNfhir-data_1.0:b2f0f237531073839bafbe0bf1fa324c163f1b3364ad4762b8dd878ba59184c4\022\rfhir-data_1.0" > 
2021-06-01 15:52:15.819 CDT [cli.lifecycle.chaincode] submitInstallProposal -> INFO 002 Chaincode code package identifier: fhir-data_1.0:b2f0f237531073839bafbe0bf1fa324c163f1b3364ad4762b8dd878ba59184c4
```

#### Approve the chaincode as Org2
Still as Org2, get the chaincode ID:
```shell
peer lifecycle chaincode queryinstalled
```

You should see a result like:
```shell
Installed chaincodes on peer:
Package ID: fhir-data_1.0:b2f0f237531073839bafbe0bf1fa324c163f1b3364ad4762b8dd878ba59184c4, Label: fhir-data_1.0
```

Approve the chaincode for Org2
```shell
export CC_PACKAGE_ID=fhir-data_1.0:b2f0f237531073839bafbe0bf1fa324c163f1b3364ad4762b8dd878ba59184c4
peer lifecycle chaincode approveformyorg -o localhost:7050 --ordererTLSHostnameOverride orderer.example.com --channelID channel1 --name fhir-data --version 1.0 --package-id $CC_PACKAGE_ID --sequence 1 --tls --cafile "${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem"
```

You should see a result like:
```shell
2021-06-01 15:58:05.614 CDT [chaincodeCmd] ClientWait -> INFO 001 txid [eb957a579478747bc19e47254e024eaae4d14f4c23888782a826c26950b789e1] committed with status (VALID) at localhost:9051
```

#### Approve the chaincode as Org1
```shell
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_ADDRESS=localhost:7051
peer lifecycle chaincode approveformyorg -o localhost:7050 --ordererTLSHostnameOverride orderer.example.com --channelID channel1 --name fhir-data --version 1.0 --package-id $CC_PACKAGE_ID --sequence 1 --tls --cafile "${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem"
```
You should see a result like:
```shell
2021-06-01 16:01:16.349 CDT [chaincodeCmd] ClientWait -> INFO 001 txid [a54c5bffb61364921927df0d05863b2e390e6a4b100c093c4c29c383b86dcaa8] committed with status (VALID) at localhost:7051
```

#### Commit the chaincode definition to the channel

Check the approvals:
```shell
peer lifecycle chaincode checkcommitreadiness --channelID channel1 --name fhir-data --version 1.0 --sequence 1 --tls --cafile "${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem" --output json
```
You should see a result like:
```shell
{
    "approvals": {
        "Org1MSP": true,
        "Org2MSP": true
    }
}
```
Commit the chaincode:
```shell
peer lifecycle chaincode commit -o localhost:7050 --ordererTLSHostnameOverride orderer.example.com --channelID channel1 --name fhir-data --version 1.0 --sequence 1 --tls --cafile "${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem" --peerAddresses localhost:7051 --tlsRootCertFiles "${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt" --peerAddresses localhost:9051 --tlsRootCertFiles "${PWD}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt"
```
You should see a result like:
```shell
2021-06-01 16:05:15.427 CDT [chaincodeCmd] ClientWait -> INFO 001 txid [771b01791594bd09a8462e33252c6a2c125ede6126aa03971ed05ce09b1ffae0] committed with status (VALID) at localhost:7051
2021-06-01 16:05:15.430 CDT [chaincodeCmd] ClientWait -> INFO 002 txid [771b01791594bd09a8462e33252c6a2c125ede6126aa03971ed05ce09b1ffae0] committed with status (VALID) at localhost:9051
```
Check the commit:
```shell
peer lifecycle chaincode querycommitted --channelID channel1 --name fhir-data --cafile "${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem"
```
You should see a result like:
```shell
Committed chaincode definition for chaincode 'fhir-data' on channel 'mychannel':
Version: 1.0, Sequence: 1, Endorsement Plugin: escc, Validation Plugin: vscc, Approvals: [Org1MSP: true, Org2MSP: true]
```

### Generate the connection json file
Generate the test-network connection-full.json file, which describes the fabric network you just deployed.  To do that, first edit connect/local-config/fabric/conf/ccp-generate.sh and set TESTNET_PATH to your test-network directory. Then generate connection-full.json:
```shell
cd connect/local-config/fabric/conf
./ccp-generate.sh
```

## Configure the client
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

That's it - you're ready to send transactions to Linux For Health and store them in your blockchain!
