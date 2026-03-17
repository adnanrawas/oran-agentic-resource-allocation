from flask import Flask, request, jsonify
import requests
import json
from api_provider import APIProvider # Import the APIProvider class from the api_provider module

app = Flask(__name__)

@app.route("/")
def home():
    return "OK", 200

@app.route("/agent", methods=["POST"])
def agent():

    data = request.json

    print("Received from agent:", data, flush=True)

    response = {
        "status": "ok",
        "message": "Master received your message"
    }

    return jsonify(response)

@app.route("/provider/openrouter", methods=["POST"])
def openrouter_proxy():
    OPENROUTER_API_KEY = APIProvider().openrouter()
    payload = request.json
    if payload is None:
        return jsonify({"error": "JSON body required"}), 400

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            # optional:
            # "HTTP-Referer": "<YOUR_SITE_URL>",
            # "X-OpenRouter-Title": "<YOUR_SITE_NAME>",
        },
        data=json.dumps({
            "model": "deepseek/deepseek-r1",
            "messages": [
                {
                    "role": "user",
                    "content": "What is the meaning of life?"
                }
            ]
        })
       
    )

    try:
        result = response.json()
    except ValueError:
        return (response.text, response.status_code, {"Content-Type": response.headers.get("Content-Type","text/plain")})

    return jsonify(result), response.status_code



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)