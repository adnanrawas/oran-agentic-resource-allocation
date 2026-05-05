import requests
import time
import os
TIMEOUT_client_server= int(os.getenv("TIMEOUT_client_server", 10))
POLL_INTERVAL_cleint = int(os.getenv("POLL_INTERVAL_cleint", 4))
payload = {
    "user_request": "I need ultra reliable low latency communication with low cost for my application"
}


user_requests = [
    {
        "id": 1,
        "user_request": "I need very low latency for remote surgery.",
        "expected_intent": "URLLC"
    },
    {
        "id": 2,
        "user_request": "I want high speed video streaming.",
        "expected_intent": "eMBB"
    },
    {
        "id": 3,
        "user_request": "I have many IoT sensors with low power.",
        "expected_intent": "mMTC"
    },
    {
        "id": 4,
        "user_request": "I need reliable communication for autonomous driving.",
        "expected_intent": "URLLC"
    },
    {
        "id": 5,
        "user_request": "I want fast internet for watching 4K videos.",
        "expected_intent": "eMBB"
    },
    {
        "id": 6,
        "user_request": "I need to connect thousands of smart meters.",
        "expected_intent": "mMTC"
    }
]

# response = requests.post(
#     "http://master:5000/optimizer_nsag2/offers",
#     json=user_requests,
#     timeout=300,
# )

# print(response.status_code)
# print(response.text)
# response.raise_for_status()

submit_response = requests.post(
    "http://master:5000/optimizer_nsag2/offers",
    json=user_requests,
    timeout=30,
)

print("SUBMIT STATUS:", submit_response.status_code)
print("SUBMIT BODY:", submit_response.text)
submit_response.raise_for_status()

job = submit_response.json()
job_id = job["job_id"]

# Step 2: poll until result is ready
while True:
    status_response = requests.get(
        f"http://master:5000/optimizer_nsag2/offers/{job_id}",
        timeout=TIMEOUT_client_server,
    )
    status_response.raise_for_status()
    data = status_response.json()

    print("JOB STATUS:", data.get("status"))

    if data.get("status") == "done":
        print("FINAL RESULT:")
        print(data)
        break

    if data.get("status") == "failed":
        print("FAILED RESULT:")
        print(data)
        raise RuntimeError(data.get("error"))

    time.sleep(POLL_INTERVAL_cleint)