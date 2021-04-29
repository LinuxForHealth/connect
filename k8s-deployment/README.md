## k8s-deployment
Enabling deployment of `Connect` and supporting services on a Kubernetes Cluster


## Getting Started

### Requirements
Deploying LinuxForHealth Connect on a Kubernetes cluster requires the following:

- A working k8s cluster - check [Minikube](https://minikube.sigs.k8s.io/) & Docker Desktop Kubernetes support
- [mkcert](https://github.com/FiloSottile/mkcert) for local trusted certificates.
- Basic know-how on creating k8s configmaps (examples provided) and enabling volume mounts in order to make signed root CA certs & keys avaiable to containers.

#### Generate trusted local certs for Connect and supporting services for your kubernetes environment
```shell
./local-config/install-certificates.sh
```
For more information on Connect and HTTPS/TLS support, please refer to [the local cert readme](../local-config/README.md).

##### Create configmaps for connect
```shell
kubectl -n <namespace-for-config-map> create configmap lfh-pemstore --from-file=lfh.pem
```
```shell
kubectl -n <namespace-for-config-map> create configmap lfh-keystore --from-file=lfh.key
```
```shell
kubectl -n <namespace-for-config-map> create configmap ca-nats --from-file=rootCA.pem
```
```shell
kubectl -n <namespace-for-config-map> create configmap nats-pemstore --from-file=nats-server.pem
```
```shell
kubectl -n <namespace-for-config-map> create configmap nats-keystore --from-file=nats-server.key
```
Please check [here](./connect/connect-deployment.yml) for an example of how these configmaps are loaded and mounted as certs for `connect`.

##### Make NATS certs available
Certs for NATS should be made available on the node(s) hosting the deployment for NATS-JS as a [`hostPath`](https://kubernetes.io/docs/concepts/storage/volumes/#hostpath) volume mount. The directory path on the host node(s) should be referenced [here](./nats-js/nats-with-jetstream.yml) under `volumes`.

### Deploying connect & Supporting Services
Example deployment yaml's are provided for reference in each of the sub-folders within this directory.
- `nats-js/` - Provides an out-of-the-box deployment for NATS Server and Jetstream – mount `/path/to/nats-server-certs/` directory with the `hostPath` directive - check [nats-with-jetstream.yml](./nats-js/nats-with-jetstream.yml) for example.
- `kafka-zk/` - Provides an out-of-the-box deployment for Kafka and ZooKeeper - exposes `localhost:9094` as the broker.
- `ibm-fhir/` - Fires up the IBM FHIR Server - documentation [here](https://ibm.github.io/FHIR/guides/FHIRServerUsersGuide/)
- `connect/` - Deploys the `connect` application to work with NATS and Kafka in the same namespace - create configmaps as described above and reference them in the deployment yaml's before connect can be deployed.

#### Helper scripts for deployment
Although the deployment yaml's in the sub-directories can be altered for achieving granular control, we provide helper shell scripts to deploy `connect` and required supporting services for users who are not familiar with tuning k8s deployments. All helper scripts require the `-n` (namespace) option.
Here are helpful descriptions for each script:
- `deployment-up.sh` - Creates the input namespace (if it doesn't exist) and deploys connect along with all supporting services (Note: Configmaps referenced in this README should be created and appropriately referenced in the yamls for all services to work correctly)
- `deployment-down.sh` - Deletes all kubernetes resources for `connect` and supporting services for the input namespace. This script does not delete the namespace.
- `delete-k8s-ns.sh` - Deletes the input kubernetes namespace. NOTE: Using this script will permanently delete all kubernetes resources on the namespace. If you are not sure what this means or if you have deployed connect and supporting services on a kuberentes namespace that has other software artifacts deployed, please do not use this script.
