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

## Build the IPFS multi-arch images
LinuxForHealth uses ipfs/go-ipfs and ipfs/ipfs-cluster docker images.  However, these images are only available on Docker Hub as amd64 images.  Follow the instructions below to build multi-arch images that support amd64, s390x and arm64.  `docker buildx` does not work for s390x builds, so build each image separately on amd64, s390x and arm64 machines and use `docker manifest` to create the multi-arch images.

### Build go-ipfs

#### Clone the repo and check out a release branch
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
On your s390x machine, first edit Dockerfile and add s390x to the [list of supported architectures](https://github.com/ipfs/go-ipfs/blob/e9b1e2d6fb916a342d0d013a3db7b88145ae5eb5/Dockerfile#L37) for tini:
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
On your s390x machine, first edit Dockerfile and add s390x to the [list of supported architectures](https://github.com/ipfs/ipfs-cluster/blob/0c01079eca925f7b62ad1984e02c6811093484b1/Dockerfile#L16) for tini:
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
