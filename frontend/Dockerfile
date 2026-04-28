FROM python:3.11-slim
WORKDIR /app
# Installing the dependencies

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "client.py"]