
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import os
import requests
import json
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

def small_donut(value, total, label, color="#3498db"):
    fig = go.Figure(
        data=[
            go.Pie(
                values=[value, max(total - value, 0)],
                labels=[label, "Remaining"],
                hole=0.65,
                marker=dict(colors=[color, "#eaeaea"]),
                textinfo="none",
                hovertemplate="%{label}: %{value}<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        height=180,
        width=180,
        margin=dict(t=10, b=10, l=10, r=10),
        showlegend=False,
    )
    return fig


@st.cache_data
def get_openrouter_generation_stats(generation_id: str) -> dict:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return {"error": "OPENROUTER_API_KEY is missing"}

    try:
        response = requests.get(
            "https://openrouter.ai/api/v1/generation",
            headers={"Authorization": f"Bearer {api_key}"},
            params={"id": generation_id},
            timeout=30,
        )
        response.raise_for_status()
        return response.json().get("data", {})
    except requests.RequestException as exc:
        return {"error": str(exc)}

def small_pie(value, total, title, color):
    fig, ax = plt.subplots(figsize=(2.2, 2.2))
    ax.pie(
        [value, max(total - value, 0)],
        colors=[color, "#eeeeee"],
        startangle=90,
        counterclock=False,
        wedgeprops={"width": 0.45}
    )
    ax.set_title(title, fontsize=10)
    ax.axis("equal")
    return fig


FILE_PATH = Path("../output/simple_state_output.json")

st.title("Radio Metrics Dashboard")

if not FILE_PATH.exists():
    st.warning(f"Waiting for result file: {FILE_PATH}")
    st.stop()

data = json.loads(FILE_PATH.read_text(encoding="utf-8"))

answer = data.get("final_answer", {}).get("answer", {})
history = data.get("metrics_history", [])
generation_id = data.get("final_answer", {}).get("raw_result", {}).get("id")


best_step = answer.get("best_step")
best_throughput = answer.get("best_throughput")
confidence = answer.get("confidence", 0)
total_steps = len(history)


col1, col2, col3, col4 = st.columns(4)


with col1:
     st.metric("Best Step", best_step+1)
     fig = small_donut(best_step+1, total_steps, "Best Step")
     st.plotly_chart(fig, use_container_width=True)

# col2.metric("Best Throughput", f"{best_throughput} Mbps")
with col2:
    st.metric("Best Throughput", f"{best_throughput} Mbps")
    fig = small_donut(best_throughput, 100, "Best Throughput")
    fig

# col3.metric("Confidence", f"{confidence * 100:.1f}%")

with col3:
    st.metric("Confidence", f"{confidence * 100:.1f}%")
    fig = small_donut(confidence, 1, "Confidence", color="#2ecc71")
    st.plotly_chart(fig, use_container_width=True)

with col4:
    st.metric("Total Steps", total_steps)
    fig = small_donut(total_steps, total_steps, "Total Steps", color="#e74c3c")
    st.plotly_chart(fig, use_container_width=True)

stats = None
if generation_id:
    stats = get_openrouter_generation_stats(generation_id)

st.subheader("Generation Info")
if generation_id and stats:
    if "error" in stats:
        st.error(stats["error"])
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Generation Time (ms)", stats.get("generation_time"))
        c2.metric("Latency (ms)", stats.get("latency"))
        c3.metric("Total Cost", stats.get("total_cost"))

        st.write("Generation ID:", generation_id)
        st.write("Model:", stats.get("model"))
        st.write("Provider:", stats.get("provider_name"))
        st.write("Created At:", stats.get("created_at"))
        st.write("Finish Reason:", stats.get("finish_reason"))

        with st.expander("Full Generation Stats"):
            st.json(stats)
else:
    st.info("No generation id found")




st.subheader("Analysis")
st.write(answer.get("analysis", "No analysis available"))

st.subheader("Decision")
st.write(answer.get("decision", "No decision available"))

# if history:
#     df = pd.DataFrame(history)
#     df.index = df.index + 1
#     df.index.name = "step"
#     st.subheader("Metrics History")
#     st.dataframe(df, use_container_width=True)
# else:
#     st.info("No metrics history yet")

if history:
    df = pd.DataFrame(history)
    df.index = df.index + 1
    df.index.name = "step"

    st.subheader("Metrics History")
    st.dataframe(df, use_container_width=True)

    st.subheader("Throughput Trend")
    st.line_chart(df["throughput"])

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("MCS by Step")
        st.bar_chart(df["mcs"])

    with col2:
        st.subheader("PRB by Step")
        st.bar_chart(df["prb"])

else:
    st.info("No metrics history yet")

with st.expander("Open Full JSON File"):
    st.json(data)