from flask import Flask, request, jsonify

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)