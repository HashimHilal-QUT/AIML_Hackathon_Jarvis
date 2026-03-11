FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/producer/market_producer.py .

CMD ["python", "market_producer.py"]
