from concurrent.futures import ThreadPoolExecutor
import uuid
from flask import Flask, request, jsonify
import requests, random
import json
from api_provider import APIProvider # Import the APIProvider class from the api_provider module
from db_connection import get_db_connection
from non_dominated_sorting_algorithm import  run_optimizer
import traceback
from pathlib import Path
import os
app = Flask(__name__)
# This is the master server that will receive the user request from the frontend, call the optimizer to get the offers, and then call the agent.
EXECUTOR = ThreadPoolExecutor(max_workers=2)
JOBS_DIR = Path("/app/output/jobs")
JOBS_DIR.mkdir(parents=True, exist_ok=True)
AGENT_URL = "http://agent:9000/select-best-offer"
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT",120))  # default = 60
#it can change depends on the model used 
MODEL_NAME = os.getenv("MODEL_NAME", "nvidia/llama-3.1-nemotron-70b-instruct") 
NSGA2_FILE = Path("/app/results/storage/baseline/nsga2_result.json")

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
def load_offers_from_file():
    data = json.loads(NSGA2_FILE.read_text(encoding="utf-8"))
    return data["front_0"]["solutions_front_0"]
# prepering the offer to be sent to the agent 
def compact_offer(offer):
    kpis = offer.get("kpis", {})

    return {
        "offer_id": offer.get("id"),
        "eMBB": {
            "cost": kpis.get("cost_eur", {}).get("eMBB"),
            "latency": kpis.get("latency_ms", {}).get("eMBB"),
            "throughput": kpis.get("throughput", {}).get("eMBB"),
        },
        "URLLC": {
            "cost": kpis.get("cost_eur", {}).get("URLLC"),
            "latency": kpis.get("latency_ms", {}).get("URLLC"),
            "throughput": kpis.get("throughput", {}).get("URLLC"),
        },
        "mMTC": {
            "cost": kpis.get("cost_eur", {}).get("mMTC"),
            "latency": kpis.get("latency_ms", {}).get("mMTC"),
            "throughput": kpis.get("throughput", {}).get("mMTC"),
        }
    }
##############################################################################################################################################
def build_multi_user_prompt(users, offers):
    return f"""
You are selecting Pareto-optimal network offers for multiple users.

Task:
- assign exactly one offer to each user
- use each offer_id at most once
- explain briefly why the offer matches the user request

KPI meaning:
- lower latency is better
- lower cost is better
- higher throughput is better


Users:
{json.dumps(users, indent=2)}

Candidate offers:
{json.dumps(offers, indent=2)}

Return JSON only in this exact format:
{{
  "assignments": [
    {{
      "user_id": "<user id>",
      "offer_id": <offer id>,
      "reason": "<short reason>"
    }}
  ]
}}
"""
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


##the basline# 
# #job in the background to run the offer
# def run_offer_selection_job(job_id, requests_payload):
#     try:
#         # sa
#         save_job(job_id, MODEL_NAME, {"status": "running", "model": MODEL_NAME})
#         raw_offers = load_offers_from_file()
#         offers = [compact_offer(offer) for offer in raw_offers]

#         users = []
#         for item in requests_payload:
#             user_request = item.get("user_request")
#             if not user_request:
#                 continue

#             users.append({
#                 "id": item.get("id"),
#                 "user_request": user_request,
#                 "expected_intent": item.get("expected_intent"),
#             })

#         if not users:
#             save_job(job_id,MODEL_NAME, {
#                 "status": "failed",
#                 "model": MODEL_NAME,
#                 "error": "No valid user_request values found"
#             })
#             return
            

#         if len(users) > len(offers):   
#             save_job(job_id, MODEL_NAME, {
#            "status": "failed",
#            "model": MODEL_NAME,
#            "error": "Number of users cannot be greater than the number of candidate offers"
#            })
#             return
         
#         prompt = build_multi_user_prompt(users, offers)

#         llm_payload = {
#             "model": MODEL_NAME,
#             "messages": [{"role": "user", "content": prompt}],
#             "response_format": {"type": "json_object"},
#             "stream": False,
#         }

#         llm_raw_result = call_openrouter(llm_payload)
#         message = llm_raw_result.get("choices", [{}])[0].get("message", {})
#         content = message.get("content")

#         if isinstance(content, str) and content.strip():
#             try:
#                 llm_selection = json.loads(content)
#             except json.JSONDecodeError:
#                 llm_selection = {"raw_content": content}
#         else:
#             llm_selection = {
#                 "raw_message": message,
#                 "raw_llm_response": llm_raw_result
#             }

#         save_job(job_id, MODEL_NAME, {
#         "status": "done",
#         "model": MODEL_NAME,
#         "total_requests": len(users),
#         "total_offers": len(offers),
#         "users": users,
#         "offers": offers,
#         "llm_selection": llm_selection
#     })

#     except Exception as exc:
#         traceback.print_exc()
#         save_job(job_id, MODEL_NAME, {
#             "status": "failed",
#             "model": MODEL_NAME,
#             "error": str(exc)
#         })
 
 ######################################################################3
 # end of the basline 

 

# calling the agnet
#job in the background to run the offer
def run_offer_selection_job(job_id, requests_payload):
    try:
        # sa
        save_job(job_id, MODEL_NAME, {"status": "running", "model": MODEL_NAME})
        raw_offers = load_offers_from_file()
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
         
        # prompt = build_multi_user_prompt(users, offers)

        # llm_payload = {
        #     "model": MODEL_NAME,
        #     "messages": [{"role": "user", "content": prompt}],
        #     "response_format": {"type": "json_object"},
        #     "stream": False,
        # }

        # llm_raw_result = call_openrouter(llm_payload)
    
        agent_response = requests.post(
        AGENT_URL,
        json={
        "users": users,
        "offers": offers
        },
        timeout=LLM_TIMEOUT
        )

        agent_response.raise_for_status()
        agent_result = agent_response.json()
        app.logger.info("agent_result=%s", agent_result)

        save_job(job_id, MODEL_NAME, {
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
       
@app.route("/optimizer_nsag2/offers", methods=["POST"])
def optimizer_offers():
    body = request.get_json(silent=True)

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
## synchronous version of the endpoint without background job for testing and development purposes
# @app.route("/optimizer_nsag2/offers", methods=["POST"])
# def optimizer_offers():
#     try:
#         body = request.get_json(silent=True)

#         if isinstance(body, list):
#             requests_payload = body
#         elif isinstance(body, dict):
#             requests_payload = body.get("requests", [])
#         else:
#             requests_payload = []

#         if not requests_payload:
#             return jsonify({
#                 "status": "failed",
#                 "error": "Missing requests list"
#             }), 400

#         print("BODY TYPE:", type(body), flush=True)
#         print("TOTAL REQUESTS:", len(requests_payload), flush=True)
#         print("FIRST ITEM:", requests_payload[0] if requests_payload else None, flush=True)

#         # optimizer_result = run_optimizer()
#         raw_offers = load_offers_from_file()[:6] # get the top 6 offers to have more options for the agent to choose from, this is just for testing and development purposes, in production we can send all the offers or implement pagination if the number of offers is too large

#         offers = [compact_offer(offer) for offer in raw_offers]
#         users = []
#         for item in requests_payload:
#             user_request = item.get("user_request")
#             if not user_request:
#                 continue

#             users.append({
#                 "id": item.get("id"),
#                 "user_request": user_request,
#                 "expected_intent": item.get("expected_intent"),
#             })

#         if not users:
#             return jsonify({
#                 "status": "failed",
#                 "error": "No valid user_request values found"
#             }), 400
#         # Ensure we have enough offers for the users
#         if len(users) > len(offers):
#             return jsonify({
#                 "status": "failed",
#                 "error": "Number of users cannot be greater than the number of candidate offers"
#             }), 400

#         prompt = build_multi_user_prompt(users, offers)
#         llm_payload = {
#             "model": "deepseek/deepseek-r1",
#             "messages": [{"role": "user", "content": prompt}],
#             "response_format": {"type": "json_object"},
#             "stream": False,
#         }
#         print("TOTAL USERS:", len(users), flush=True)
#         print("TOTAL OFFERS:", len(offers), flush=True)
#         llm_raw_result = call_openrouter(llm_payload)
#         message = llm_raw_result.get("choices", [{}])[0].get("message", {})
#         content = message.get("content", "{}")
#         try:
#             llm_selection = json.loads(content)
#         except json.JSONDecodeError:
#             llm_selection = {"raw_content": content}

#         return jsonify({
#             "status": "success",
#             "total_requests": len(users),
#             "total_offers": len(offers),
#             "users": users,
#             "offers": offers,
#             "llm_selection": llm_selection,
#             "raw_llm_response": llm_raw_result,
#         }), 200

#     except Exception as exc:
#         traceback.print_exc()
#         return jsonify({
#             "status": "failed",
#             "error": str(exc)
#         }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

###########################################################################################################################################
