from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Dict, List, Annotated
import operator
from flask import Flask, request, jsonify
import json
import aiohttp
import os
import requests
app = Flask(__name__)

# url for api provider to call the openrouter api an structure the user request and offers to be used in the intent extraction and similarity search
MASTER_URL = "http://master:5000/provider/openrouter"

################################################################################################################################
#getting the input from the state and prepare it for intent extraction using API and matrics similarity search

import json
import aiohttp
import os

MASTER_URL = "http://master:5000/provider/openrouter"

class AgentState(TypedDict, total=False):
    # user request in text and manually created  next step to use from the frontend
    user_request: str

    offers: List[Dict[str, object]]
    #intent structure in json format:
    intent: Dict[str, object]

    evaluated_offers: Annotated[List[Dict[str, object]],operator.add]

    selected_offer: Dict[str, object]
    # i should use human and agent messages instead of logs, but for simplicity, i will just use logs

    logs: Annotated[List[str], operator.add]


#########################################################################################################################################
# I need the function to get the user requst and offer to prepeare for some similarity search and intent extraction.
def test_intent_node(state: AgentState):
    #get the user request and offers
    user_request = state["user_request"].lower()
    return {
        "intent": {
            "raw_request": user_request,
            "slice_type": "unknown",
            "priority": "general",
            "requirements": {},
            "intent_summary": "Intent extraction not implemented yet."
        },
        "logs": [f"intent_node -> received user request: {user_request}"]
    }


    
def get_int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def intent_node(state: AgentState):
    user_request = state["user_request"]

    prompt = f"""
You are an intent extraction agent for 5G network slicing.

User request:
{user_request}

Extract the intent and return JSON only.

Required JSON format:

{{
  "raw_request": "{user_request}",
  "slice_type": "eMBB | URLLC | mMTC | unknown",
  "priority": "low_latency | high_throughput | low_cost | massive_connectivity | reliability | general",
  "requirements": {{
    "latency": "low | medium | high | unknown",
    "throughput": "low | medium | high | unknown",
    "cost": "low | medium | high | unknown",
    "reliability": "low | medium | high | unknown"
  }},
  "intent_summary": "short explanation"
}}
"""

    data = {
        "model": "deepseek/deepseek-r1",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"},
        "stream": False
    }

    try:
        # timeout = aiohttp.ClientTimeout(total=get_int_env("LLM_TIMEOUT", 120))

        # async with aiohttp.ClientSession(timeout=timeout) as session:
        #     async with session.post(MASTER_URL, json=data) as response:
        #         raw_text = await response.text()

        response = requests.post(
        MASTER_URL,
        json=data,
        timeout=120
        )

        # result = json.loads(raw_text)
        response.raise_for_status()
        result = response.json()

        message = result.get("choices", [{}])[0].get("message", {})
        content = message.get("content", "{}")

        intent = json.loads(content)

        return {
            "intent": intent,
            "logs": [f"intent_node -> extracted intent: {intent}"]
        }

    except Exception as exc:
        return {
            "intent": {
                "raw_request": user_request,
                "slice_type": "unknown",
                "priority": "general",
                "requirements": {},
                "intent_summary": "Intent extraction failed.",
                "error": str(exc)
            },
            "logs": [f"intent_node error: {exc}"]
        }

##################################################################################################################################



def build_graph():

    graph = StateGraph(AgentState)

    graph.add_node("intent_node", intent_node)

    graph.add_edge(START, "intent_node")
    graph.add_edge("intent_node", END)

    return graph.compile()

graph_app = build_graph()


# getting the user request and save it in the state and invoke the graph for metrics similarity search and intent extraction          
@app.route("/select-best-offer", methods=["POST"])
def select_best_offer():
    body = request.get_json()
    user_request = body.get("user_request")
    offers = body.get("offers")
    print("Received user request:")
    if not user_request:
        return jsonify({"status": "failed", "error": "Missing user_request"}), 400

    if not offers:
        return jsonify({"status": "failed", "error": "Missing offers"}), 400
     # saving the user request and offers to be used in the next node   
    state = {
        "user_request": user_request,
        "offers": offers,
        "logs": ["Received request and offers"]
    }
    # calling the graph app to run the intent extraction and similarity search
    final_state = graph_app.invoke(state)

    return jsonify(final_state)
    # temporary test response
    # return jsonify({
    #     "status": "success",
    #     "message": "Agent received data",
    #     # "user_request": user_request,
    #     "offers_count": len(offers)
    # }), 200










if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9000)