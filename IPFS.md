# IPFS

## Overview
Connect IPFS Support is an incubating feature. IPFS is not integrated but is available for research purposes.

### Create Swarm Key for a private IPFS peer network
```shell
docker run --rm golang:1.9 sh -c 'go get github.com/Kubuxu/go-ipfs-swarm-key-gen/ipfs-swarm-key-gen && ipfs-swarm-key-gen'
/key/swarm/psk/1.0.0/
/base16/
f744ccf21ef090407977a33e01deb0a0c6a3397ae0366ff6f3c749e200f2510d
```
Persist the generated output (example above) to `./private-ipfs-network/.ipfs/swarm.key`

### Create IPFS Cluster Secret (32-bit hex-encoded string) and update `CLUSTER_SECRET` in `docker-compose.yml`
```shell
openssl rand -hex 32
```

### To launch IPFS
```
docker-compose --profile ipfs up -d
```
