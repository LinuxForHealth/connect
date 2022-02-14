"""
Load data for LinuxForHealth LPR testing

Run this script once to set up patient records for locust lpr testing.
"""
import httpx
import json
import os


num_files = int(os.getenv("NUM_FILES", 6))
base_url = str(os.getenv("BASE_URL", "https://127.0.0.1:5000"))
messages = []


for file_num in range(1, num_files + 1):
    file = "./messages/fhir" + str(file_num) + ".json"
    with open(file) as f:
        print(f"Loading message file = {file}")
        messages.append(json.load(f))

for message in messages:
    resource_type = message["resourceType"]
    result = httpx.post(f"{base_url}/fhir/{resource_type}", verify=False, json=message)
    print(f"Posted patient record for resource type {resource_type}, result = {result}")
