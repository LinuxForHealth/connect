#!/bin/sh

CHAINCODE=fhir-data@1.0.0.tar.gz
CHANNELID=channel1
NAME=fhir-data
VERSION=1.0
echo Chaincode = ${CHAINCODE}

echo Installing the contract as Org1
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=localhost:7051
peer lifecycle chaincode install ${CHAINCODE}

echo Installing the contract as Org2
export CORE_PEER_LOCALMSPID="Org2MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org2.example.com/users/Admin@org2.example.com/msp
export CORE_PEER_ADDRESS=localhost:9051
peer lifecycle chaincode install ${CHAINCODE}

INSTALLED=`peer lifecycle chaincode queryinstalled`
CC_PACKAGE_ID=`echo ${INSTALLED} | cut -d " " -f 7 | cut -d "," -f 1`
echo Package ID = ${CC_PACKAGE_ID}

echo Approving the contract as Org2
export CC_PACKAGE_ID=${CC_PACKAGE_ID}
peer lifecycle chaincode approveformyorg \
-o localhost:7050 \
--ordererTLSHostnameOverride orderer.example.com \
--channelID ${CHANNELID} \
--name ${NAME} \
--version ${VERSION} \
--package-id ${CC_PACKAGE_ID} \
--sequence 1 \
--tls \
--cafile "${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem"

echo Approving the contract as Org1
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_ADDRESS=localhost:7051
peer lifecycle chaincode approveformyorg \
-o localhost:7050 \
--ordererTLSHostnameOverride orderer.example.com \
--channelID ${CHANNELID} \
--name ${NAME} \
--version ${VERSION} \
--package-id ${CC_PACKAGE_ID} \
--sequence 1 \
--tls \
--cafile "${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem"

echo Commiting the contract
peer lifecycle chaincode commit \
-o localhost:7050 \
--ordererTLSHostnameOverride orderer.example.com \
--channelID ${CHANNELID} \
--name ${NAME} \
--version ${VERSION} \
--sequence 1 \
--tls \
--cafile "${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem" \
--peerAddresses localhost:7051 \
--tlsRootCertFiles "${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt" \
--peerAddresses localhost:9051 \
--tlsRootCertFiles "${PWD}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt"

echo Verifying the committed contract
peer lifecycle chaincode querycommitted \
--channelID ${CHANNELID} \
--name ${NAME} \
--cafile "${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem"
