## k8s-deployment
Enabling deployment of `pyConnect` and supporting services on a Kubernetes Cluster


## Getting Started

### Requirements
Deploying LinuxForHealth pyConnect on a Kubernetes cluster requires the following:

- A working k8s cluster (check (Minikube)[https://minikube.sigs.k8s.io/] & Docker Desktop Kubernetes server support)
- [mkcert](https://github.com/FiloSottile/mkcert) for local trusted certificates.
- Basic know-how on creating k8s configmaps (examples provided) and enabling volume mounts in order to make signed root CA certs & keys avaiable to containers.

#### Generate trusted local certs for pyConnect and supporting services

```shell
./local-certs/install-certificates.sh
```
For more information on pyConnect and HTTPS/TLS support, please refer to [the local cert readme](../local-certs/README.md).

#### Create configmaps for pyconnect
```shell
--WIP--
```
