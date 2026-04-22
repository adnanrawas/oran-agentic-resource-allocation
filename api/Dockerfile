FROM python:3.9-slim
# setting the working directory in the container
WORKDIR /app

RUN apt-get update && apt-get install -y curl

# Copy the requirements file into the container
COPY requirements.txt .

# Installing the dependencies
RUN pip install -r requirements.txt

# Copy the Flask application code into the container
COPY . .

# Expose the port the Flask application will be running on
EXPOSE 5000

# CMD ["python", "non_dominated_sorting_algorithm_2.py"]

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "120", "--graceful-timeout", "120", "server:app"]