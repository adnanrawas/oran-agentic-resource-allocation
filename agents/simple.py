from senario_phase1 import get_metrics
import json
import operator
from datetime import datetime
import asyncio
import os
from langgraph.graph import END, StateGraph, START
from pathlib import Path
from typing import Annotated, Dict, List, TypedDict
import aiohttp
MASTER_URL = "http://master:5000/provider/openrouter"
STATE_FILE = Path(__file__).with_name("simple_state_output.json")


class AgentState(TypedDict,total=False):
    agent_name: str
    counter: int
    saved_to: str
    metrics_history: Annotated[List[Dict[str, object]], operator.add]
    logs: Annotated[List[str], operator.add]
    final_answer: Dict[str, object]
    
 
##############################################################################

def get_int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default

def should_continue(state: AgentState):
    if state["counter"] < 5:
        return "fetch_metrics"
    return "llm_reasoning"


async def llm_reasoning(state: AgentState):
    prompt = f"""
You are analyzing radio network performance over time.

We collected 5 steps of metrics:

{json.dumps(state['metrics_history'], indent=2)}

Instructions:

- Identify which step has the BEST throughput
- Analyze how MCS changes relative to PRB

- Select the BEST overall PRB allocation step considering both throughput and MCS
- Provide a final decision

Return your answer in JSON format:

{{
  "best_step": <index>,
  "best_throughput": <value>,
  "analysis": "...",
  "decision": "...",
  "confidence": 0-1
}}
"""
    data = {
      "model": "deepseek/deepseek-r1",
      "messages": [
        {"role":"user","content": prompt}   
      ]
    }

    # print("PROMPT SENT:", prompt) #debugging: print the prompt being sent to the LLM
    try:
         LLM_TIMEOUT = get_int_env("LLM_TIMEOUT", 120)
         timeout = aiohttp.ClientTimeout(total=LLM_TIMEOUT)
         async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(MASTER_URL, json=data) as response:
                raw_text = await response.text()
                print("STATUS:", response.status)
                print("RAW RESPONSE:", raw_text)
    except aiohttp.ClientError as exc:
                    return {
                        "final_answer": {
                            "model": data["model"],
                            "status_code": None,
                            "reasoning": None,
                            "answer": None,
                            "raw_result": str(exc),
                        },
                        "logs": [f"LLM request error: {exc}"]
                      }

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError:  
             return {
             "final_answer": {
            "model": data["model"],
            "status_code": response.status,
            "reasoning": None,
            "answer": None,
            "raw_result": raw_text,
        },
        "logs": ["LLM response was not valid JSON"]
        }
    message = result.get("choices", [{}])[0].get("message", {})
    content = message.get("content")
    reasoning = message.get("reasoning_content")
    parsed_answer = None
    if content:
        try:
            parsed_answer = json.loads(content)
        except json.JSONDecodeError:
            parsed_answer = {"raw_text": content}
    out = {
            "model": data["model"],
            "status_code": response.status,
            "reasoning": reasoning,
            "answer": parsed_answer,
            "raw_result": result
        }
        
    return {
        "final_answer":out,
        "logs": [f"LLM decision: {out}"]
    }

##############################################################################3 
# This is a simple example of a LangGraph workflow that fetches radio metrics, saves the state..
async def fetch_metrics(state: AgentState) -> Dict[str, object]:
    metric = await get_metrics()
    return {
        "counter": state["counter"] + 1,
        "metrics_history": [metric],
        "logs": [f"fetch_metrics -> {metric}"],
    }

# i shoud save in the database 
def save_state(state: AgentState) -> Dict[str, object]:
    snapshot = {
        "agent_name": state["agent_name"],
        "counter": state["counter"],
        "metrics_history": state["metrics_history"],
        "final_answer": state.get("final_answer"),
    }
    Path(state["saved_to"]).write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    return {
        "logs": [f"save_state -> saved to {state['saved_to']}"]
    }


# def build_graph():
#     workflow = StateGraph(AgentState)
#     workflow.add_node("fetch_metrics", fetch_metrics)
#     workflow.add_node("save_state", save_state)
#     workflow.set_entry_point("fetch_metrics")
#     workflow.add_edge("fetch_metrics", "save_state")
#     workflow.add_edge("save_state", END)
#     return workflow.compile()

def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("fetch_metrics", fetch_metrics)
    graph.add_node("llm_reasoning", llm_reasoning)
    graph.add_node("save", save_state)
    graph.add_edge(START, "fetch_metrics")
    graph.add_conditional_edges(
        "fetch_metrics",
        should_continue,
        {
            "fetch_metrics": "fetch_metrics",
            "llm_reasoning": "llm_reasoning"
        }
    )
     # after LLM → save once
    graph.add_edge("llm_reasoning", "save")

    # then END
    graph.add_edge("save", END)

    return graph.compile()

            
def print_graph(app) -> None:
    print("\nLangGraph Workflow")
    print("START -> fetch_metrics -> (loop until counter == 5) -> llm_reasoning -> save -> END")
    print("\nMermaid:")
    try:
        print(app.get_graph().draw_mermaid())
    except Exception as exc:
        print(f"Graph view unavailable: {exc}")


async def main() -> None:
    app = build_graph()
    print_graph(app)
    png_bytes = app.get_graph().draw_mermaid_png()

# Save it to the current directory (/app)
    filename = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / filename
    output_path.write_bytes(png_bytes)
    print(f"Image saved to: {os.getcwd()}/output/{filename}")    # Render and save to a high-quality PNG
    # save_attractive_graph(app)
    # initial_state: AgentState = {"agent_name": "Agent1", "counter": 0,"metrics_history": []}
    initial_state: AgentState = {
    "agent_name": "Agent1",
    "counter": 0,
    "metrics_history": [],
    "saved_to": str(STATE_FILE),
    }
    final_state = await app.ainvoke(initial_state)


    print("\nFinal state:")
    print(json.dumps(final_state, indent=2))

    print("\nSaved file:")
    print(initial_state["saved_to"])


if __name__ == "__main__":
        asyncio.run(main())
