"""
Load test LinuxForHealth REST APIs using locust.
"""
import json
import os
import resource
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
    resource.setrlimit(resource.RLIMIT_NOFILE, (999999, 999999))

    @task
    def post_patient(self):
        msg_num = randint(0, num_files - 1)
        resource_type = messages[msg_num]["resourceType"]
        msg = messages[msg_num]
        self.client.post("/fhir/" + resource_type, verify=False, json=messages[msg_num])

    @task
    def get_data(self):
        self.client.get(
            "/data?dataformat=FHIR-R4&partition=0&offset=0",
            verify=False,
            name="/data",
        )

    @task
    def get_status(self):
        self.client.get(
            "/status",
            verify=False,
        )

    def on_start(self):
        self.client.verify = False
