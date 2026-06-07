from concurrent.futures import ThreadPoolExecutor
import uuid
from flask import Flask, request, jsonify
import requests, random
import json
from datetime import datetime
from api_provider import APIProvider # Import the APIProvider class from the api_provider module
from db_connection import get_db_connection
from non_dominated_sorting_algorithm import  run_optimizer
import traceback
from pathlib import Path
# Import the TOPSIS helpers used to rank and persist baseline results.
from algo_mcdm.topsis import DEFAULT_USE_CASES, rank_use_cases, save_rankings
import os
import time
#naming the output folder
app = Flask(__name__)
# This is the master server that will receive the user request from the frontend, call the optimizer to get the offers, and then call the agent.
EXECUTOR = ThreadPoolExecutor(max_workers=2)
JOBS_DIR = Path("/app/output/jobs")
JOBS_DIR.mkdir(parents=True, exist_ok=True)
AGENT_URL = "http://agent:9000/select-best-offer"
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT",120))  # default = 120
#it can change depends on the model used 
MODEL_NAME = os.getenv("MODEL_NAME", "nvidia/llama-3.1-nemotron-70b-instruct") 
NSGA2_FILE = Path("/app/results/storage/baseline/nsga2_low_congestion.json")
TOPSIS_RESULTS_DIR = NSGA2_FILE.parent / "topsis"

#client will call /optimizer_nsag2/offers endpoint 
#first function is called by the client and then agent start############################################################       
@app.route("/optimizer_nsag2/offers", methods=["POST"])
def optimizer_offers():
    
    body = request.get_json(silent=True) #taking the user request from the body of the body request  

    if isinstance(body, list):
        requests_payload = body 
    elif isinstance(body, dict):
        requests_payload = body.get("requests", [])
    else:
        requests_payload = []

    if not requests_payload:
        return jsonify({
            "status": "failed",
            "error": "Missing requests list"
        }), 400

    job_id = str(uuid.uuid4())
    save_job(job_id, MODEL_NAME, {"status": "queued", "model": MODEL_NAME})
    EXECUTOR.submit(run_offer_selection_job, job_id, requests_payload)

    return jsonify({
        "status": "queued",
        "job_id": job_id
    }), 202
#first function is called by the client and then agent end############################################################     
#client will call /optimizer_nsag2/offers -> endpoint  -> caling start job (agent call) and wait for the result in the background and save it in the local file and then client will call /optimizer_nsag2/offers/<job_id> to get the result of the job
# second caling the agnet to run the loop and select the best offer 
#job in the background to run the offer
def run_offer_selection_job(job_id, requests_payload):
    try:
        save_job(job_id, MODEL_NAME, {"status": "running", "model": MODEL_NAME})
        raw_offers = load_offers_from_file() # loading the offer from local file 
        offers = [compact_offer(offer) for offer in raw_offers]

        users = []
        for item in requests_payload:
            user_request = item.get("user_request")
            if not user_request:
                continue

            users.append({
                "id": item.get("id"),
                "user_request": user_request,
                "expected_intent": item.get("expected_intent"),
            })

        if not users:
            save_job(job_id,MODEL_NAME, {
                "status": "failed",
                "model": MODEL_NAME,
                "error": "No valid user_request values found"
            })
            return
            

        if len(users) > len(offers):   
            save_job(job_id, MODEL_NAME, {
           "status": "failed",
           "model": MODEL_NAME,
           "error": "Number of users cannot be greater than the number of candidate offers"
           })
            return
         
        # Step 1: start agent job
        start = requests.post(
        f"{AGENT_URL}/start",
        json={
            "users": users,
            "offers": offers
        },
        timeout=10
    )
        start.raise_for_status()

        agent_job_id = start.json()["agent_job_id"]

        deadline = time.monotonic() + LLM_TIMEOUT + 30

        while time.monotonic() < deadline:
            r = requests.get(f"{AGENT_URL}/jobs/{agent_job_id}", timeout=10)
            r.raise_for_status()
            agent_data = r.json()

            if agent_data["status"] == "done":
                agent_result = agent_data["result"]
                break

            if agent_data["status"] == "failed":
                raise RuntimeError(agent_data.get("error", "Agent failed"))

            time.sleep(5)
        else:
            raise TimeoutError("Agent job polling timed out")
        # agent_response.raise_for_status()
        # agent_result = agent_response.json()
        # app.logger.info("agent_result=%s", agent_result)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
 
        save_job(job_id, MODEL_NAME, {
        "created_at": timestamp,    
        "status": "done",
        "model": MODEL_NAME,
        "total_requests": len(users),
        "total_offers": len(offers),
        "users": users,
        "offers": offers,
        "llm_selection": agent_result
    })

    except Exception as exc:
        traceback.print_exc()
        save_job(job_id, MODEL_NAME, {
            "status": "failed",
            "model": MODEL_NAME,
            "error": str(exc)
        })
###################################################### end of server agent call############################################################
###################################################### utilities functions ##################################################################

def job_file(job_id, name_of_model):
    safe_model = name_of_model.replace("/", "_").replace(":", "_").replace(" ", "_")
    return JOBS_DIR / f"{job_id}_{safe_model}.json"

def save_job(job_id, name_of_model, payload):
    job_file(job_id, name_of_model).write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8"
    )
def load_job(job_id, name_of_model):
    path = job_file(job_id, name_of_model)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
# URL for the agent container to call run the loop graph


def get_top_3_offers_nsag2():
    raw_optimizer_json = get_optimizer_nsag2()
    #convert the raw json string to a python dictionary
    data = json.loads(raw_optimizer_json)
    # get Pareto front solutions
    slice_offers = data["front_0"]["solutions_front_0"][:3]

    return slice_offers
###################################################### end utilities functions ##################################################################
@app.route("/")
def home():
    return "OK", 200
#######################################################################################################################
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
##########################################     #############################################################################

@app.route("/agent", methods=["POST"])
def agent():

    data = request.json

    print("Received from agent:", data, flush=True)

    response = {
        "status": "ok",
        "message": "Master received your message"
    }

    return jsonify(response)

############################################## calling the provider Cloud #######################################################################
@app.route("/provider/openrouter", methods=["POST"])
def openrouter_proxy():
    # getting the openRouter api key using the api Provider class
    OPENROUTER_API_KEY = APIProvider().openrouter()
    if not OPENROUTER_API_KEY:
        return jsonify({"error": "OPENROUTER_API_KEY is not configured"}), 500

    payload = request.json
    if payload is None:
        return jsonify({"error": "JSON body required"}), 400

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                # optional:
                # "HTTP-Referer": "<YOUR_SITE_URL>",
                # "X-OpenRouter-Title": "<YOUR_SITE_NAME>",
            },
            data=json.dumps(payload),
            timeout=LLM_TIMEOUT,
        )
    except requests.RequestException as exc:
        return jsonify({"error": "Failed to reach OpenRouter", "details": str(exc)}), 502
    try:
        result = response.json()
        print("OpenRouter response:", result, flush=True)
    except ValueError:
        return (
            response.text,
            response.status_code,
            {"Content-Type": response.headers.get("Content-Type", "text/plain")},
        )

    return jsonify(result), response.status_code

############################################## calling the provider Cloud end   #######################################################################
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

# This endpoint will return the top 3 offers from the optimizer using the NSAG2 algorithm.
# @app.route("/optimizer_nsag2/offers", methods=["POST"])
# def optimizer_offers():
#     try:
#         body = request.get_json()
#         user_request = body.get("user_request") # get the user request from the body of the post request
#         offers = run_optimizer()
#         agent_response = requests.post(
#             AGENT_URL,
#             json={
#                 "user_request": user_request,
#                 "offers": offers
#             },
#             timeout=120
#         )

#         # agent_response.raise_for_status()
#         # # Get the JSON response from the agent container
#         agent_result = agent_response.json()
#         return jsonify({
#             "status": "success",
#              "user_request":user_request,
#              "offers": offers,
#              "agent_response": agent_result
#         }), 200

#     except Exception as exc:
#         return jsonify({"status": "failed", "error": str(exc)}), 500


###########################################################################################################################################
# load the offer from local file instead of running the optimizer to save time during development and testing
def load_nsga2_data_from_file():
    return json.loads(NSGA2_FILE.read_text(encoding="utf-8"))


def load_offers_from_file():
    data = load_nsga2_data_from_file()
    return data["front_0"]["solutions_front_0"]

######################################################################################################################
def get_topsis_rankings(save_results=True):
    data = load_offers_from_file()
    rankings = rank_use_cases(data=data, use_cases=DEFAULT_USE_CASES, weights=[1, 1, 1, 1])

    if save_results:
        return save_rankings(rankings, output_dir=TOPSIS_RESULTS_DIR, source_json=NSGA2_FILE)

    return rankings
#####################################################################################################################
#####################################################################################################################
@app.route("/ranking/topsis", methods=["GET", "POST"])
def ranking_topsis():
    try:
        body = request.get_json(silent=True) if request.method == "POST" else None
        save_arg = request.args.get("save")
        save_results = True

        if isinstance(body, dict) and "save" in body:
            save_value = body["save"]
            if isinstance(save_value, str):
                save_results = save_value.strip().lower() not in {"0", "false", "no"}
            else:
                save_results = bool(save_value)
        elif save_arg is not None:
            save_results = save_arg.strip().lower() not in {"0", "false", "no"}

        payload = get_topsis_rankings(save_results=save_results)
        return jsonify({
            "status": "success",
            "saved": save_results,
            **payload,
        }), 200
    except FileNotFoundError:
        return jsonify({
            "status": "failed",
            "error": f"NSGA-II result file not found: {NSGA2_FILE}"
        }), 404
    except Exception as exc:
        app.logger.exception("ranking_topsis failed")
        return jsonify({
            "status": "failed",
            "error": str(exc)
        }), 500
#####################################################################################################################

# prepering the offer to be sent to the agent 
def compact_offer(offer):
    kpis = offer.get("kpis", {})

    return {
        "offer_id": offer.get("id"),
        "eMBB": {
            "cost": kpis.get("cost_eur", {}).get("eMBB"),
            "latency": kpis.get("latency_ms", {}).get("eMBB"),
            "throughput": kpis.get("throughput", {}).get("eMBB"),
            "energy": kpis.get("energy", {}).get("eMBB")
        },
        "URLLC": {
            "cost": kpis.get("cost_eur", {}).get("URLLC"),
            "latency": kpis.get("latency_ms", {}).get("URLLC"),
            "throughput": kpis.get("throughput", {}).get("URLLC"),
            "energy": kpis.get("energy", {}).get("URLLC")
        },
        "mMTC": {
            "cost": kpis.get("cost_eur", {}).get("mMTC"),
            "latency": kpis.get("latency_ms", {}).get("mMTC"),
            "throughput": kpis.get("throughput", {}).get("mMTC"),
            "energy": kpis.get("energy", {}).get("mMTC")
        }
    }
##############################################################################################################################################
#TEST to be replaced with proxy to openrouter
def call_openrouter(payload):
    OPENROUTER_API_KEY = APIProvider().openrouter()
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not configured")

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        data=json.dumps(payload),
        timeout=180,
    )
    response.raise_for_status()
    return response.json()

###########################################################################################################################

@app.route("/optimizer_nsag2/offers/<job_id>", methods=["GET"])
def optimizer_offers_status(job_id):
    data = load_job(job_id, MODEL_NAME)
    if not data:
        return jsonify({
            "status": "failed",
            "error": "Job not found"
        }), 404
    return jsonify(data), 200

###########################################################################################################################
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

###########################################################################################################################################
###############flow#####################

#. client → server
#  "Start the job"

#2. server → client
#   "OK, job_id = abc123"

#3. background job:
#   server → agent → LLM → agent → server
#   server saves result

#4. client → server
#   "What is status of job_id abc123?"

#5. server → client
 #2  "running" or "done" + result
