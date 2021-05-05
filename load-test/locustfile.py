"""
Load test LinuxForHealth REST APIs using locust.  Example:
    cd connect/load-test
    locust --host https://localhost:5000 --run-time 5m --users 500 --spawn-rate 20 --headless

By default, this load test POSTs to /fhir using randomly selected FHIR resources from
connect/load-test/messages/fhir[1...NUM_FILES].json files.  To separate FHIR resources,
place them in separate files.

Override the number of resource files (default = 2) on the command line with NUM_FILES.
This example:
    NUM_FILES=1 locust --host https://localhost:5000 --run-time 15s --users 100 --spawn-rate 20 --headless
loads the following files:
Loading message file = ./messages/fhir1.json
"""
import json
import os
from locust import task, between
from locust.contrib.fasthttp import FastHttpUser
from random import randint


num_files = int(os.getenv("NUM_FILES", 2))
messages = []

for file_num in range(1, num_files + 1):
    file = "./messages/fhir" + str(file_num) + ".json"
    with open(file) as f:
        print(f"Loading message file = {file}")
        messages.append(json.load(f))


class QuickstartUser(FastHttpUser):
    wait_time = between(1, 2.5)

    @task
    def post_patient(self):
        msg_num = randint(0, num_files - 1)
        resource_type = messages[msg_num]["resourceType"]
        msg = messages[msg_num]
        self.client.post("/fhir/" + resource_type, verify=False, json=messages[msg_num])

    @task
    def get_data(self):
        self.client.get(
            "/data?dataformat=FHIR-R4_PATIENT&partition=0&offset=0",
            verify=False,
            name="/data",
        )

    def on_start(self):
        self.client.verify = False
