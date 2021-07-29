# IPFS

## Overview
LinuxForHealth connect IPFS support provides for replication of data to the connect private IPFS cluster.  The connect IPFS Cluster and IPFS node start when you start the connect services from the top-level connect directory.

### Change Swarm Key
To change the private IPFS network swarm key:
```shell
docker run --rm golang:1.9 sh -c 'go get github.com/Kubuxu/go-ipfs-swarm-key-gen/ipfs-swarm-key-gen && ipfs-swarm-key-gen'
/key/swarm/psk/1.0.0/
/base16/
f744ccf21ef090407977a33e01deb0a0c6a3397ae0366ff6f3c749e200f2510d
```
Persist the generated output (example above) to `./private-ipfs-network/swarm.key`

### Change IPFS Cluster Secret
To change the IPFS cluster secret (32-bit hex-encoded string), run the following and update `CLUSTER_SECRET` in `docker-compose.yml`:
```shell
openssl rand -hex 32
```
