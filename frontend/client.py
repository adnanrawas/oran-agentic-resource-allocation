import requests

payload = {
    "user_request": "I need ultra reliable low latency communication with low cost for my application"
}

response = requests.post(
    "http://master:5000/optimizer_nsag2/offers",
    json=payload,
    timeout=30,
)

response.raise_for_status()
print(response.json())
