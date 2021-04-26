# Connect
LinuxForHealth Connectors for Inbound Data Processing

## Where to Contribute  
| Type      | Link |
| ----------- | ----------- |
| 🚨 Bug Reports | [GitHub Issues Tracker](https://github.com/LinuxForHealth/connect/labels/bug) |  
| 🎁 Feature Requests & Ideas | [GitHub Issues Tracker](https://github.com/LinuxForHealth/connect/issues)  | 
| ❔ Questions | [LFH Slack Channel](https://ibm-watsonhealth.slack.com/archives/G01639WJEMA) |   
| 🚙 Roadmap | [Project Board](https://github.com/LinuxForHealth/connect/projects/1) |


## Getting Started

### Read the Documentation
The [LinuxForHealth documentation](https://linuxforhealth.github.io/docs/) includes architectural overviews, development guidelines, and deployment options.

### Required Software
The LinuxForHealth Connect development environment requires the following:

- [git](https://git-scm.com) for project version control
- [mkcert](https://github.com/FiloSottile/mkcert) for local trusted certificates
- [Python 3.8 or higher](https://www.python.org/downloads/mac-osx/) for runtime/coding support
- [Pipenv](https://pipenv.pypa.io) for Python dependency management  
- [Docker Compose](https://docs.docker.com/compose/install/) for a local container runtime

For Windows 10 users, we suggest using [Windows Subsystem for Linux](https://docs.microsoft.com/en-us/windows/wsl/install-win10)

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

#### Black code formatting integration
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

#### Generate trusted local certs for connect and supporting services
```shell
./local-certs/install-certificates.sh
```
For more information on connect and HTTPS/TLS support, please refer to [the local cert readme](./local-certs/README.md).


#### Start connect and supporting services
```shell
docker-compose up -d
docker-compose ps
pipenv run connect
```

Browse to `https://localhost:5000/docs` to view the Open API documentation

### Docker Image
The connect docker image is an "incubating" feature and is subject to change. The image is associated with the "deployment" profile to provide separation from core services.

#### Build the image
The connect image build integrates the application's x509 certificate (PEM encoded) into the image.

The `APPLICATION_CERT_PATH` build argument is used to specify the location of the certificate on the host machine.
If the `APPLICATION_CERT_PATH` build argument is not provided, a default value of ./local-certs/lfh.pem is used.

#### Build the image with Docker CLI
```shell
docker build --build-arg APPLICATION_BUILD_CERT_PATH=./local-certs/ -t linuxforhealth/connect:0.42.0 .
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

## Links and Resources 
| Type      | Link |
| ----------- | ----------- |
| 📰 Documentation | [LinuxForHealth Docs Site](https://linuxforhealth.github.io/docs/) |  
| 📰 Documentation | [IPFS](./IPFS.md) |  
