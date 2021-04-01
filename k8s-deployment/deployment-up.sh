#!/bin/bash


show_help() {
  echo
  echo "USAGE: ./{path_to-> deployment_up.sh} -n {k8s_ns}"
  echo
  echo "OPTIONS:"
  echo "-n (namespace)  Provide a kubernetes namespace for which deployments should be created."
  echo
}

### Parse arguments section
OPTIND=1  # Reset in case getopts has been used previously in the shell.
k8s_ns=""

while getopts "h?n:" opt; do
  case "$opt" in
  h|\?)
    show_help
    exit 0
    ;;
  n)
    k8s_ns=$OPTARG
    ;;
  esac
done

if [ -z "$k8s_ns" ]
then
  echo \"namespace\" option not specified
  show_help
  exit 0
fi


### Create Kubernetes resources for Nats, Kafka, ZK and IBM FHIR Server
echo ### Creating kubernetes namespace: $k8s_ns ###
kubectl create ns $k8s_ns
echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

sleep 2  # Safety measure sleep for extremely slow k8s clusters
echo

echo ### Deploying NATS with Jetstream Service ###
kubectl apply -f ./nats-js/nats-with-jetstream.yml --namespace=$k8s_ns
echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

sleep 5
echo

echo ### Deploying Kafka & Zookeeper Service ###
kubectl apply -f ./kafka-zk/kafka-zookeeper.yml --namespace=$k8s_ns
echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

sleep 5
echo

echo ### Deploying IBM FHIR Server ###
kubectl apply -f ./ibm-fhir/ibm-fhir-server.yml --namespace=$k8s_ns
echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

sleep 5
echo

echo ### Deploying pyconnect application ###
kubectl apply -f ./pyconnect/pyconnect-deployment.yml --namespace=$k8s_ns
echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

