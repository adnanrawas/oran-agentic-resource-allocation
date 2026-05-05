FROM python:3.11-slim
WORKDIR /app
COPY . .
# Installing the dependencies
RUN pip install -r requirements.txt
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
# CMD ["python", "agent.py"]
# CMD ["python", "senario_phase1.py"]
# CMD ["python", "graph_state.py"]

# CMD ["python", "simple.py"]

CMD ["python", "agent_validation_loop.py"]


