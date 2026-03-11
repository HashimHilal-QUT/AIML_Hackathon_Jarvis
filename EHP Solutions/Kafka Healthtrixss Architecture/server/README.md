# Kafka Data Processing Service

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start services:
```bash
docker-compose up -d
```

3. Run tests:
```bash
pytest
```

## API Documentation

### Process Data
POST /api/v1/process
- Accepts JSON file
- Returns request ID for tracking

### Check Status
GET /api/v1/status/<request_id>
- Returns processing status and results

## Configuration

Environment variables:
- KAFKA_BOOTSTRAP_SERVERS
- REDIS_HOST
- REDIS_PORT
