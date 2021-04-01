#!/bin/bash
  

show_help() {
  echo
  echo "USAGE: ./{path_to-> deployment_down.sh} -n {k8s_ns}"
  echo
  echo "OPTIONS:"
  echo "-n (namespace)  Provide a kubernetes namespace for which deployments should be deleted."
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


### Delete Kubernetes resources for Nats, Kafka, ZK and IBM FHIR Server
echo
echo "### Tearing down NATS with Jetstream Service ###"
kubectl delete -f ./nats-js/nats-with-jetstream.yml --namespace=$k8s_ns
echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

sleep 5
echo

echo "### Tearing down Kafka & Zookeeper Service ###"
kubectl delete -f ./kafka-zk/kafka-zookeeper.yml --namespace=$k8s_ns
echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

sleep 5
echo

echo "### Tearing down IBM FHIR Server ###"
kubectl delete -f ./ibm-fhir/ibm-fhir-server.yml --namespace=$k8s_ns
echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

sleep 5
echo

echo "### Tearing down pyconnect Application ###"
kubectl delete -f ./pyconnect/pyconnect-deployment.yml --namespace=$k8s_ns
echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


echo
echo "Manually delete K8S namespace or run delete-k8s-ns.sh script"
echo
