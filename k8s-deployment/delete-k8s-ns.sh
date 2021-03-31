#!/bin/bash
  

show_help() {
  echo
  echo "USAGE: ./{path_to-> delete_k8s_ns.sh} -n {k8s_ns}"
  echo
  echo "OPTIONS:"
  echo "-n (namespace)  Provide a kubernetes namespace that needs to be deleted"
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


### Delete Kubernetes namespace

echo ### Deleting Kubernetes namespace ###
kubectl delete ns $k8s_ns
echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

