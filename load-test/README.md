# LinuxForHealth Connect Load Tests
LinuxForHealth connect load tests use [locust](https://locust.io) to test REST APIs.

**Note:** LinuxForHealth connect implements a default message rate limit of 5 messages/second.  To load test, run connect with an increased rate limit, such as 10000.  To change the default rate limit, add an environment variable to connect/.env:
```shell
# change the default connect rate limit
CONNECT_RATE_LIMIT=10000/second
```
or specify CONNECT_RATE_LIMIT when starting LinuxForHealth connect:
```shell
CONNECT_RATE_LIMIT=10000/second pipenv run connect
```
or update connect/config.py with the new rate limit:
```shell
connect_rate_limit: str = "10000/second"
```
## Run the Tests

### Example 1
Use the provided FHIR resource files to test LinuxForHealth connect /fhir and /data endpoints:
```shell
cd connect/load-test
locust --host https://localhost:5000 --run-time 5m --users 500 --spawn-rate 20 --headless
```
### Example 2
By default, this load test POSTs to /fhir using randomly selected FHIR resources from connect/load-test/messages/fhir[1...NUM_FILES].json files.  You can replace the contents of these fhir*.json files with your own FHIR resources or add fhir resource files to connect/load-test/messages using the same naming convention.  To separate FHIR resources, place them in separate files.  To change the number of files used by the load test (default = 2):
```shell
cd connect/load-test
NUM_FILES=1 locust --host https://localhost:5000 --run-time 5m --users 500 --spawn-rate 20 --headless
```
Result:  
Loading message file = ./messages/fhir1.json

### Example 3
To use the locust UI to run load tests, run locust from the command line:
```shell
locust --host https://localhost:5000
```
then point your browser to [http://127.0.0.1:8089](http://127.0.0.1:8089) to run the tests and vary the number of users and spawn rate.
