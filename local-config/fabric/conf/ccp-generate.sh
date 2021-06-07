#!/bin/bash
#
# Generate a full connection profile for test-network, so that fabric-network discovery is not
# required, facilitating fabric-network client operation in a docker container.
#
# Based on the Hyperledger Fabric test-network connection profile generator in hyperledger/fabric-samples.
#

# Set the path to your test-network deployment on your local machine
TESTNET_PATH=/Users/ccorley@us.ibm.com/go/src/github.com/ccorley/fabric-samples/test-network

function one_line_pem {
    echo "`awk 'NF {sub(/\\n/, ""); printf "%s\\\\\\\n",$0;}' $1`"
}

function json_ccp {
    local P1P=$(one_line_pem $6)
    local P2P=$(one_line_pem $7)
    local O1P=$(one_line_pem $8)
    local C1P=$(one_line_pem $9)
    local C2P=$(one_line_pem ${10})
    sed -e "s/\${P1PORT}/$1/" \
        -e "s/\${P2PORT}/$2/" \
        -e "s/\${O1PORT}/$3/" \
        -e "s/\${CA1PORT}/$4/" \
        -e "s/\${CA2PORT}/$5/" \
        -e "s#\${PEER1PEM}#$P1P#" \
        -e "s#\${PEER2PEM}#$P2P#" \
        -e "s#\${O1PEM}#$O1P#" \
        -e "s#\${CA1PEM}#$C1P#" \
        -e "s#\${CA2PEM}#$C2P#" \
        ./ccp-template.json
}

P1PORT=7051
P2PORT=9051
O1PORT=7050
CA1PORT=7054
CA2PORT=8054
PEER1PEM=${TESTNET_PATH}/organizations/peerOrganizations/org1.example.com/tlsca/tlsca.org1.example.com-cert.pem
PEER2PEM=${TESTNET_PATH}/organizations/peerOrganizations/org2.example.com/tlsca/tlsca.org2.example.com-cert.pem
O1PEM=${TESTNET_PATH}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/tls/tlscacerts/tls-localhost-9054-ca-orderer.pem
CA1PEM=${TESTNET_PATH}/organizations/peerOrganizations/org1.example.com/ca/ca.org1.example.com-cert.pem
CA2PEM=${TESTNET_PATH}/organizations/peerOrganizations/org2.example.com/ca/ca.org2.example.com-cert.pem

echo "$(json_ccp $P1PORT $P2PORT $O1PORT $CA1PORT $CA2PORT $PEER1PEM $PEER2PEM $O1PEM $CA1PEM $CA2PEM)" > ./connection-full.json
