# Connect
LinuxForHealth Connectors for Inbound Data Processing


![Supported Versions](https://img.shields.io/badge/python%20version-3.8%2C%203.9-blue)
![Connect CI](https://github.com/linuxforhealth/connect/actions/workflows/connect-ci.yml/badge.svg)
![Image Build](https://github.com/linuxforhealth/connect/actions/workflows/connect-image-build.yml/badge.svg)
![GitHub Issues](https://img.shields.io/github/issues/LinuxForHealth/connect)
![GitHub Forks](https://img.shields.io/github/forks/LinuxForHealth/connect)
![GitHub Stars](https://img.shields.io/github/stars/LinuxForHealth/connect)
![GitHub License](https://img.shields.io/github/license/LinuxForHealth/connect)  
[![Cauldron Report](https://img.shields.io/badge/Cauldron%20Report-View%20Project%20Metrics-brightgreen)](https://cauldron.io/project/4148)  



## Where to Contribute  
| Type      | Link |
| ----------- | ----------- |
| 🚨 Bug Reports | [GitHub Issues Tracker](https://github.com/LinuxForHealth/connect/labels/bug) |  
| 🎁 Feature Requests & Ideas | [GitHub Issues Tracker](https://github.com/LinuxForHealth/connect/issues)  | 
| ❔ Questions | [LFH Slack Channel](https://ibm-watsonhealth.slack.com/archives/G01639WJEMA) |   
| 🚙 Roadmap | [Project Board](https://github.com/LinuxForHealth/connect/projects/1#workspaces/linux-for-health-5ee2d7cecec5920ec43ae1cb/board?notFullScreen=false&repos=337464130) |


## Getting Started

### Read the Documentation
The [LinuxForHealth documentation](https://linuxforhealth.github.io/docs/) includes architectural overviews, development guidelines, and deployment options.

### Required Software
The LinuxForHealth Connect development environment requires the following:

- [git](https://git-scm.com) for project version control
- [mkcert](https://github.com/FiloSottile/mkcert) for local trusted certificates
- [Python 3.8 or higher](https://www.python.org/downloads/mac-osx/) for runtime/coding support
- [Pipenv](https://pipenv.pypa.io) for Python dependency management  
- [Docker Compose 1.28.6 or higher](https://docs.docker.com/compose/install/) for a local container runtime

For Windows 10 users, we suggest using [Windows Subsystem for Linux](https://docs.microsoft.com/en-us/windows/wsl/install-win10).    
For s390x users, please read these [instructions](./platforms/s390x/README.md) before beginning.  
For arm64 users, please read these [instructions](./platforms/arm64/README.md) before beginning.

### Set Up A Local Environment
#### Clone the project and navigate to the root directory
```shell
git clone https://github.com/LinuxForHealth/connect
cd connect
```

#### Confirm that Python build tooling, pip and pipenv are installed
```shell
pip --version
pipenv --version
```

#### Install core and dev dependencies
```shell
pip install --upgrade pip
pipenv sync --dev
```

#### Run tests
```shell
pipenv run pytest
```

#### Start connect and supporting services
```shell
docker-compose up -d
docker-compose ps
pipenv run connect
```
For s390x users, please follow these [instructions](./platforms/s390x/README.md) to run connect.

Browse to `https://localhost:5000/docs` to view the Open API documentation

### Generate new trusted local certs for connect and supporting services (optional)
Perform this step to create new certificates for connect and connect services. The creation of new certificates is not required, as connect contains a set of default certificates for SSL.  If you do create new certificates, you must rebuild the connect docker image, as described in the next section.
```shell
./local-config/install-certificates.sh
```
For more information on connect and HTTPS/TLS support, please refer to [the local cert readme](local-config/README.md).  
For s390x users, please read these [instructions](./platforms/s390x/README.md).  
For arm64 users, please read these [instructions](./platforms/arm64/README.md).

### Docker Image
The connect docker image is an "incubating" feature and is subject to change. The image is associated with the "deployment" profile to provide separation from core services.

#### Build the image
The connect image build integrates the application's x509 certificate (PEM encoded) into the image.

The `APPLICATION_CERT_PATH` build argument is used to specify the location of the certificate on the host machine.
If the `APPLICATION_CERT_PATH` build argument is not provided, a default value of ./local-certs/lfh.pem is used.

#### Build the image with Docker CLI
```shell
docker build --build-arg APPLICATION_BUILD_CERT_PATH=./local-config/ -t linuxforhealth/connect:0.42.0 .
```

#### Build the image with Docker-Compose
The docker-compose command below parses the build context, arguments, and image tag from the docker-compose.yaml file.
```shell
docker-compose build connect
```

#### Run connect and Supporting Services
```shell
docker-compose --profile deployment up -d
```

### Developing for connect: Black code formatting integration
LinuxForHealth connect utilizes the [black library](https://black.readthedocs.io/en/stable/index.html) to provide standard code formatting. Code formatting and style are validated as part of the [LinuxForHealth connect ci process](./.github/workflows/connect-ci.yml). LinuxForHealth connect provides developers with an option of formatting using pipenv scripts, or a git pre-commit hook.

#### Pipenv Scripts

##### Check for formatting errors
```shell
pipenv run check-format
```

##### Format code
```shell
pipenv run format
```

#### Git pre-commit hook integration

##### Install git pre-commit hooks (initial setup)
```shell
pipenv run pre-commit install
```

##### Commit Output - No Python Source Committed
```shell
black................................................(no files to check)Skipped
[black-formatter 95bb1c6] settings black version to latest release
 1 file changed, 1 insertion(+), 1 deletion(-)
```

##### Commit Output - Python Source is Correctly Formatted
```shell
black....................................................................Passed
[format-test c3e1b4a] test commit
 1 file changed, 1 insertion(+)
```

##### Commit Output - Black Updates Python Source
```shell
black....................................................................Failed
- hook id: black
- files were modified by this hook

reformatted connect/routes/api.py
All done! ✨ 🍰 ✨
1 file reformatted.
```
## Build multi-arch docker image 
LinuxForHealth connect runs on amd64, arm64 & s390x platforms.  Follow these instructions to build the multi-arch image that supports all these platforms.  At this time, you need access to all 3 platforms in order to build the multi-arch image.

### Build the amd64 and arm64 image
Run `docker buildx` to build an image that supports amd64 and arm64.  The s390x image has to be built separately, for now.
```shell
docker buildx build --pull --push --platform linux/amd64,linux/arm64 --build-arg APPLICATION_BUILD_CERT_PATH=./local-config/ -t linuxforhealth/connect:0.42.0 .
```

### Pull, tag and push the amd64 image
On your amd64 machine:
```shell
docker pull linuxforhealth/connect:0.42.0
docker images
docker image tag <image_id> linuxforhealth/connect:0.42.0-amd64
docker push linuxforhealth/connect:0.42.0-amd64
```

### Pull, tag and push the arm64 image
On your arm64 device:
```shell
docker pull linuxforhealth/connect:0.42.0
docker images
docker image tag <image_id> linuxforhealth/connect:0.42.0-arm64
docker push linuxforhealth/connect:0.42.0-arm64
```

### Build, tag and push the s390x image
On your s390x machine, build the s390x connect image using these [instructions](./platforms/s390x/README.md), then tag and push the image:
```shell
docker images
docker image tag <image_id> linuxforhealth/connect:0.42.0-s390x
docker push linuxforhealth/connect:0.42.0-s390x
```

### Create the multi-arch image
Use `docker manifest` to create the multi-arch image for all 3 platforms and push it:
```shell
docker manifest create \                                         
linuxforhealth/connect:0.42.0 \
--amend linuxforhealth/connect:0.42.0-s390x \
--amend linuxforhealth/connect:0.42.0-amd64 \
--amend linuxforhealth/connect:0.42.0-arm64

docker manifest push linuxforhealth/connect:0.42.0
```
That's it - you can now run `docker pull linuxforhealth/connect:0.42.0` on all 3 platforms.

## Links and Resources 
| Type      | Link |
| ----------- | ----------- |
| 📰 Documentation | [LinuxForHealth Docs Site](https://linuxforhealth.github.io/docs/) |  
| 📰 Documentation | [IPFS](local-config/ipfs/README.md) |  
