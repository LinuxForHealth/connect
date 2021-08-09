# IPFS

## Overview
LinuxForHealth IPFS support provides for replication of data from connect to the private IPFS cluster.  The connect IPFS Cluster and IPFS node start automatically when you start the connect services from the top-level connect directory.

### Configure the IPFS private network
The LinuxForHealth IPFS cluster sits on top of an IPFS private network and facilitates automatic data replication between nodes in the private network.  To configure the private IPFS network, perform the following with LinuxForHealth running.  Start with the LinuxForHealth node that will be the IPFS bootstrap node.

Exec into the bootstrap ipfs-node-0 container:
```shell
docker exec -it ipfs-node-0 sh
```
Get the bootstrap node id (the value of the "ID" field):
```shell
ipfs id
```
Using the bootstrap node id and the bootstrap machine's IP address, add the bootstrap node. Note this command because you will re-use it exactly on the other IPFS nodes:
```shell
ipfs bootstrap add /ip4/<bootstrap_machine_IP>/tcp/4001/ipfs/<bootstrap_node_id>
# Example:
#   ipfs bootstrap add /ip4/1.2.3.4/tcp/4001/ipfs/12D3KooWN6MRLbbhVDyNVDmgkUmgsfT7kuXMWSTGU7PPabcdefg
```

Exit the ipfs-node-0 container and stop it:
```shell
exit
docker stop ipfs-node-0
```

Repeat the same ipfs add command for each LinuxForHealth node in the private network, then restart each ipfs-node-0 container, starting with the bootstrap node:
```shell
docker start ipfs-node-0
```
Note:  If you delete a container after configuring it, you will need to run the configuration again.  Particularly, `docker-compose down` will remove the containers.

### Test the IPFS private network
To test the LinuxForHealth IPFS network, send FHIR data to LinuxForHealth connect.  In the result, you'll see an IPFS link, such as:
```shell
"ipfs_uri": "/ipfs/Qmassczcq4pZ2MQh4cj5emaueZmxTUfD6gcQ84j7jkAVMt",
```
You can retrieve the stored data from any IPFS server on a private IPFS network node in the LinuxForHealth network.  Examples:
```shell
http://localhost:8080/ipfs/Qmassczcq4pZ2MQh4cj5emaueZmxTUfD6gcQ84j7jkAVMt
http://1.2.3.4:8080/ipfs/Qmassczcq4pZ2MQh4cj5emaueZmxTUfD6gcQ84j7jkAVMt
```

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

## Build the IPFS multi-arch images
LinuxForHealth uses ipfs/go-ipfs and ipfs/ipfs-cluster docker images.  However, these images are only available on Docker Hub as amd64 images.  Follow the instructions below to build multi-arch images that support amd64, s390x and arm64.  `docker buildx` does not work for s390x builds, so build each image separately on amd64, s390x and arm64 machines and use `docker manifest` to create the multi-arch images.

Note:  As a LinuxForHealth deployer, you should not need to rebuild the IPFS images unless you are adding a supported OS.

### Build go-ipfs

#### Clone the repo and check out a release branch
On each platform clone the repo and check out the correct branch for the release:
```shell
git clone https://github.com/ipfs/go-ipfs.git
cd go-ipfs
git checkout release-v0.9.1
```

#### Build, tag and push the amd64 image
On your amd64 machine:
```shell
docker build -t linuxforhealth/go-ipfs:release-v0.9.1-amd64 .
docker push linuxforhealth/go-ipfs:release-v0.9.1-amd64
```

#### Build, tag and push the arm64 image
On your arm64 device:
```shell
docker build -t linuxforhealth/go-ipfs:release-v0.9.1-arm64 .
docker push linuxforhealth/go-ipfs:release-v0.9.1-arm64
```

#### Build, tag and push the s390x image
On your s390x machine, first edit the Dockerfile and add s390x to the [list of supported architectures](https://github.com/ipfs/go-ipfs/blob/e9b1e2d6fb916a342d0d013a3db7b88145ae5eb5/Dockerfile#L37) for tini:
```shell
"amd64" | "armhf" | "arm64" | "s390x")
```
then build, tag and push the s390x image:
```shell
docker build -t linuxforhealth/go-ipfs:release-v0.9.1-s390x .
docker push linuxforhealth/go-ipfs:release-v0.9.1-s390x
```

#### Create the multi-arch image
Use `docker manifest` to create the multi-arch image for all 3 platforms and push it:
```shell
docker manifest create \
linuxforhealth/go-ipfs:release-v0.9.1 \
--amend linuxforhealth/go-ipfs:release-v0.9.1-s390x \
--amend linuxforhealth/go-ipfs:release-v0.9.1-amd64 \
--amend linuxforhealth/go-ipfs:release-v0.9.1-arm64

docker manifest push linuxforhealth/go-ipfs:release-v0.9.1 --purge
```

### Build ipfs-cluster

#### Clone the repo and check out a tagged release
On each platform clone the repo and check out the correct tag for the release:
```shell
git clone https://github.com/ipfs/ipfs-cluster.git
cd ipfs-cluster
git checkout v0.14.0
```

#### Build, tag and push the amd64 image
On your amd64 machine:
```shell
docker build -t linuxforhealth/ipfs-cluster:v0.14.0-amd64 .
docker push linuxforhealth/ipfs-cluster:v0.14.0-amd64
```

#### Build, tag and push the arm64 image
On your arm64 device:
```shell
docker build -t linuxforhealth/ipfs-cluster:v0.14.0-arm64 .
docker push linuxforhealth/ipfs-cluster:v0.14.0-arm64
```

#### Build, tag and push the s390x image
On your s390x machine, first edit the Dockerfile and add s390x to the [list of supported architectures](https://github.com/ipfs/ipfs-cluster/blob/0c01079eca925f7b62ad1984e02c6811093484b1/Dockerfile#L16) for tini:
```shell
"amd64" | "armhf" | "arm64" | "s390x")
```
then build, tag and push the s390x image:
```shell
docker build -t linuxforhealth/ipfs-cluster:v0.14.0-s390x .
docker push linuxforhealth/ipfs-cluster:v0.14.0-s390x
```

#### Create the multi-arch image
Use `docker manifest` to create the multi-arch image for all 3 platforms and push it:
```shell
docker manifest create \
linuxforhealth/ipfs-cluster:v0.14.0 \
--amend linuxforhealth/ipfs-cluster:v0.14.0-s390x \
--amend linuxforhealth/ipfs-cluster:v0.14.0-amd64 \
--amend linuxforhealth/ipfs-cluster:v0.14.0-arm64

docker manifest push linuxforhealth/ipfs-cluster:v0.14.0 --purge
```
