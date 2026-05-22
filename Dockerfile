FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY agents/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY agents/ ./agents/
COPY data/    ./data/

RUN mkdir -p /tmp/data

ENV DB_PATH=/tmp/healthcare.db

RUN python data/generate_dataset.py

EXPOSE 8000

CMD ["uvicorn", "agents.main:app", "--host", "0.0.0.0", "--port", "8000"]