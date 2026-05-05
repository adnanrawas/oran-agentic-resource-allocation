from concurrent.futures import ThreadPoolExecutor
import os, logging, traceback, json
from flask import Flask, request, jsonify
from langgraph.graph import StateGraph, START, END
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import TypedDict, Dict, List, Annotated
import operator
import re
import time
from pathlib import Path
import uuid


# client side agent 
import requests

class AgentState(TypedDict, total=False):

    users: List[Dict[str, object]] #offers list by users
    offers: List[Dict[str, object]] #offers list by the optimizer
    analyzed_selection: Dict[str, object] # analysis of the llm selection from the intent analyzer node 
    llm_selection: Dict[str, object] # selection by the llm
    validation_result: Dict[str, object] # result of the validation metrics calculation
    validator_feedback: Dict[str, object] # feedback from the validator
    final_selection: Dict[str, object] # final selection after validation
    logs: Annotated[List[str], operator.add]

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"
#####################################################
#variables     
MASTER_URL = "http://master:5000/provider/openrouter"
# MODEL_NAME = "deepseek/deepseek-r1"
MODEL_NAME = os.getenv("MODEL_NAME", "nvidia/llama-3.1-nemotron-70b-instruct") 
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT",120))  
JOBS_DIR=Path("/app/output/agent_jobs")
JOBS_DIR.mkdir(parents=True, exist_ok=True)

####################################################


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "agent running"}), 200
# start background job 
@app.post("/select-best-offer/start")
def start_agent():
    data = request.json
    agent_job_id = str(uuid.uuid4())

    EXECUTOR.submit(run_agent_job, agent_job_id, data)

    return jsonify({
        "agent_job_id": agent_job_id,
        "status": "queued"
    }), 202

def run_agent_job(agent_job_id, data):
    save_agent_job(agent_job_id, {"status": "running"})

    # LLM call here (can take 5 min)
    result = call_llm(data)

    save_agent_job(agent_job_id, {
        "status": "done",
        "result": result
    })

@app.get("/jobs/<agent_job_id>")
def get_agent_job(agent_job_id):
    return jsonify(load_agent_job(agent_job_id))

def save_agent_job(agent_job_id, data):
    job_file = JOBS_DIR / f"{agent_job_id}.json"

    with open(job_file, "w") as f:
        json.dump(data, f)

def load_agent_job(agent_job_id):
    job_file = JOBS_DIR / f"{agent_job_id}.json"

    if not job_file.exists():
        return {"status": "not_found"}

    with open(job_file, "r") as f:
        return json.load(f)


def intent_analyzer_node(state: AgentState):
    
    users = state["users"] #offers list by users
    # anlyze the user request and extract intent using llm and return the intent structure to be used in the similarity search and offer evaluation.
    prompt = f"""
                You are a 6G network slicing intent analysis agent.
                Extract structured intent from each user's natural language request.
                Do NOT select offers — another agent handles that later.

                # Rules
                - If the user EXPLICITLY mentions a number (e.g., "5ms", "100 Mbps", "$20/month"),extract it into the numeric field.
                - If the user does NOT mention numbers, leave numeric fields as null 
                  and infer only the qualitative level (low / medium / high).
                - NEVER invent or guess numbers the user did not state.
                - Use "unknown" only when the request is too vague to infer even qualitatively.
                - Rank priorities by what matters most to the user.


                Users:
                {json.dumps(users, indent=2)}

                Return JSON only in this format:

                {{
                "analyzed_users": [
                    {{
                    "user_id": "user id",
                    "use_case": "gaming | streaming | IoT | industrial | AR/VR | browsing | ...",
                    "slice_type": "eMBB | URLLC | mMTC | unknown",
                    "requirements": {{
                    "latency":     {{ "level": "low | medium | high | unknown", "max_ms":    null }},
                    "throughput":  {{ "level": "low | medium | high | unknown", "min_mbps":  null }},
                    "cost":        {{ "level": "low | medium | high | unknown", "max_cost":  null }},
                    }},
                     "priority_ranking": ["latency", "throughput", "cost"],
                    "intent_summary": "one-sentence plain English summary",
                    }}
                ]
                }}
                """
    data = {
            "model": "deepseek/deepseek-r1",
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
            "stream": False
        }
    try: 
        result = call_llm(data)
       
        content = (
        result.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "{}")
    ) 
        # Remove <think>...</think> blocks (DeepSeek R1 reasoning)
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
        # Remove markdown code fences
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
        analyzed_selection = json.loads(content)
        start = time.time()
        app.logger.info("intent_analyzer start")
        app.logger.info("intent_analyzer done in %.2fs", time.time() - start)
        return {
            "analyzed_selection": analyzed_selection,
            "logs": ["intent analyzer completed"]
        }

    except Exception as exc:

            return {
                    "analyzed_selection": {
                        "analyzed_users": [],
                        "error": str(exc)
                    },
                    "logs": [f"intent analyzer error: {exc}"]
                }

@retry(stop=stop_after_attempt(1), wait=wait_exponential(min=1, max=5))
def call_llm(data):
    response = requests.post(
        MASTER_URL,
        json=data,
        timeout=LLM_TIMEOUT 
    )

    response.raise_for_status()
    return response.json()

# select the best offer for each user based on the analyzed intent 
def offer_selection_node(state: AgentState):
    offers = state["offers"]
    analyzed_selection = state["analyzed_selection"]
    feedback = state.get("validator_feedback")   

    prompt = f"""
    You are a 6G network slicing offer selection agent.

    Your task is to select the best available offer for each user based on the
    analyzed user intent and the user's priority ranking.

    # Hard Rules
    - Select ONLY from the provided candidate offers. Never invent offers.
    - Each user gets exactly one offer.
    - You MUST return `selected_offer_id` for every assigned user.
    - Copy `selected_offer_id` EXACTLY from the chosen candidate offer's `offer_id`.
    - Each offer_id can be used at most once.
    - Copy selected_slice_type EXACTLY from the chosen offer; do not infer.
    - If offers are fewer than users, assign to highest-priority users first;
    set selected_offer_id to null for unassigned users.

    # Selection Logic
    - Choose the offer that best satisfies the user's requirements.
    - Give more importance to the user's highest-ranked priority.
    - Lower latency is better. Higher throughput is better. Lower cost is better.
    - If a numeric hard requirement cannot be fully met, pick the closest offer
    and flag it in the reason field: "CONSTRAINT_VIOLATION: <detail>".

    # Conflict Resolution
    - Prioritize by slice criticality: URLLC > eMBB > mMTC
    - Stricter explicit requirements (user-stated numbers) take precedence
     "Stricter" = lower max_ms, higher min_mbps, lower max_cost.
    - Use your 6G domain expertise to resolve any remaining edge cases 

    # Feedback Handling
    - If feedback lists rejected offers for a user, do NOT pick them again for that user.
    - Address the specific validation issues mentioned.
    - Prefer offers with better SLA alignment than the previously rejected ones.

    # Data

    ## Analyzed user intents
    {json.dumps(analyzed_selection, indent=2)}

    ## Candidate offers
    {json.dumps(offers, indent=2)}

    ## Previous validator feedback
    {json.dumps(feedback, indent=2) if feedback else "None — first attempt"}

    # Output (raw JSON only, no markdown, no trailing commas)
    {{
    "assignments": [
        {{
        "user_id": "user id",
        "selected_offer_id": "exact offer_id from candidate offers or null",
        "selected_slice_type": "copied exactly from the chosen offer",
        "priority_used": "latency | throughput | cost | balanced",
        "reason": "short explanation with specific numbers; include CONSTRAINT_VIOLATION if any"
        }}
    ]
    }}
    """  

    data = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "stream": False
    }

    try:
        result = call_llm(data)

        content = (
            result.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "{}")
        )

        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)

        llm_selection = json.loads(content)

        return {
            "llm_selection": llm_selection,
            "logs": ["offer selection completed"]
        }

    except Exception as exc:
        return {
            "llm_selection": {
                "assignments": [],
                "error": str(exc)
            },
            "logs": [f"offer selection error: {exc}"]
        }
#############################################################################################################################################

# next step 

def calculate_validation_metrics():
    # calculate how well the selected offer matches the user requirements and priorities.
    # return a dict of metrics to be used in the validation node for feedback and improvement.
    pass


def validator_node(state: AgentState):
    # validate the selected offers based on the calculated metrics and provide feedback for improvement.
    pass


def build_graph():

    graph = StateGraph(AgentState)

    graph.add_node("intent_analyzer_node", intent_analyzer_node)
    graph.add_node("offer_selection_node", offer_selection_node)

    graph.add_edge(START, "intent_analyzer_node")
    graph.add_edge("intent_analyzer_node", "offer_selection_node")
    graph.add_edge("offer_selection_node", END)

    return graph.compile()    


graph_app = build_graph()


@app.route("/select-best-offer", methods=["POST"])
def select_best_offer():

    try:

        body = request.get_json()

        users = body.get("users", [])
        offers = body.get("offers", [])

        state = {
            "users": users,
            "offers": offers,
            "logs": ["request received"]
        }

        final_state = graph_app.invoke(state)

        return jsonify({
            "status": "success",
            "result": final_state
        }), 200

    except Exception as exc:
        app.logger.exception("select_best_offer failed")
        return jsonify({
            "status": "failed",
            "error": str(exc),
            "traceback": traceback.format_exc() if DEBUG_MODE else None
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9000)
#                
#Intent Analyzer
#↓
#Offer Selection
#↓
#Validation Metrics Calculation
#↓
#Validator
#↓
#Feedback Loop if needed        

# next TM Forum compliance inve and knowledge base 