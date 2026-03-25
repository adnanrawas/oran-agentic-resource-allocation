from flask import Flask, request, jsonify
import requests, random
import json
from api_provider import APIProvider # Import the APIProvider class from the api_provider module
from db_connection import get_db_connection


app = Flask(__name__)


@app.route("/")
def home():
    return "OK", 200


@app.route("/db/check")
def db_check():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM oran_metrics LIMIT 1;")
                result = cur.fetchone()

        return jsonify({"status": "connected", "result": result}), 200
    except Exception as exc:
        return jsonify({"status": "failed", "error": str(exc)}), 500

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
    # getting the openRouter api key using the api Provider class
    OPENROUTER_API_KEY = APIProvider().openrouter() 
    print("Using OpenRouter API Key:", OPENROUTER_API_KEY, flush=True)
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
        data=json.dumps(payload)
       )

    try:
        result = response.json()
    except ValueError:
        return (response.text, response.status_code, {"Content-Type": response.headers.get("Content-Type","text/plain")})

    return jsonify(result), response.status_code

# This is a mock endpoint to simulate radio metrics for the agent.
@app.route("/radio-metrics", methods=["GET"])
def get_metrics():
    try:
        data = {
            "throughput": random.randint(200,600),
            "mcs": random.randint(5,28),
            "prb": random.randint(10,100)
        }
        return jsonify(data)
    except Exception as exc:
           return jsonify({"status": "failed", "error": str(exc)}), 500



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)