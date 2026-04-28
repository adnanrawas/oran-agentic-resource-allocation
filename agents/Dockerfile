FROM python:3.11-slim
WORKDIR /app
COPY . .
# Installing the dependencies
RUN pip install -r requirements.txt
# CMD ["python", "agent.py"]
# CMD ["python", "senario_phase1.py"]
# CMD ["python", "graph_state.py"]

# CMD ["python", "simple.py"]

CMD ["python", "exp1_simple_loop_similarity_search.py"]
