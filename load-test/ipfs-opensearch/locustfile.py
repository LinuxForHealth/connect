"""
Load test LinuxForHealth REST APIs using locust.
"""
import os
from locust import task, between
from locust.contrib.fasthttp import FastHttpUser
from random import randint


num_patients = int(os.getenv("NUM_PATIENTS", 2))


class QuickstartUser(FastHttpUser):
    wait_time = between(1, 2.5)

    @task
    def get_lpr(self):
        patient_num = randint(1, num_patients)
        self.client.get(
            f"/data/lpr?patient_id=00{patient_num}",
            verify=False,
            name=f"/data/lpr?patient_id=00{patient_num}",
        )

    def on_start(self):
        self.client.verify = False
