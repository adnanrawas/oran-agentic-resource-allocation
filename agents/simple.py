from senario_phase1 import get_metrics
import json
import operator
import subprocess
import os
from mmdc import MermaidConverter
from pathlib import Path
from typing import Annotated, Dict, List, TypedDict
from langgraph.graph import END, StateGraph
import asyncio
METRICS_URL = "http://master:5000/radio-metrics"
STATE_FILE = Path(__file__).with_name("simple_state_output.json")


class AgentState(TypedDict):
    agent_name: str
    counter: int
    saved_to: str
    metrics_history: Annotated[List[Dict[str, float]], operator.add]

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
    }
    Path(state["saved_to"]).write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    return {
        "logs": [f"save_state -> saved to {state['saved_to']}"]
    }


def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("fetch_metrics", fetch_metrics)
    workflow.add_node("save_state", save_state)
    workflow.set_entry_point("fetch_metrics")
    workflow.add_edge("fetch_metrics", "save_state")
    workflow.add_edge("save_state", END)
    return workflow.compile()

# def save_attractive_graph(app, filename="./agent_graph.png"):
#     # 1. Get the Mermaid string
#     mermaid_text = app.get_graph().draw_mermaid()
    
#     # 2. Initialize the converter
#     converter = MermaidConverter()
    
#     # 3. Generate and save the PNG
#     # The library writes the file directly to the path provided
#     converter.to_png(mermaid_text, filename)
    
#     # Check if it actually exists to confirm
#     if os.path.exists(filename):
#         print(f"✅ Success! {filename} is saved in your app directory.")
#     else:
#         print("❌ File was not created. Check folder permissions.")

            
def print_graph(app) -> None:
    print("\nSimple LangGraph Workflow")
    print("START -> fetch_metrics -> save_state -> END")
    print("\nMermaid:")
    try:
        print(app.get_graph().draw_mermaid())
    except Exception as exc:
        print(f"Graph view unavailable: {exc}")


async def main() -> None:
    app = build_graph()
    print_graph(app)
    # Render and save to a high-quality PNG
    # save_attractive_graph(app)
    initial_state: AgentState = {"agent_name": "Agent1", "counter": 0,"metrics_history": [], "saved_to": str(STATE_FILE)}
    final_state = await app.ainvoke(initial_state)

    print("\nFinal state:")
    print(json.dumps(final_state, indent=2))

    print("\nSaved file:")
    print(STATE_FILE)


if __name__ == "__main__":
    asyncio.run(main())
