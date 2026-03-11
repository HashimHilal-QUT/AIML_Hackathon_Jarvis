# Enterprise Kafka-Based Data Processing System

## System Architecture Overview

```ascii
┌──────────────┐     ┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  Client API  │────▶│   Kafka     │────▶│  Processor   │────▶│   Storage    │
│  (Flask)     │     │   Cluster   │     │  Service     │     │   (Redis)    │
└──────────────┘     └─────────────┘     └──────────────┘     └──────────────┘
       ▲                                         │                    │
       │                                         │                    │
       └─────────────────────────────────────────┴────────────────────
                            Status Updates
```

## Server-Side Components

### 1. Project Structure

server/
├── docker/
│   ├── Dockerfile.api
│   ├── Dockerfile.processor
│   └── docker-compose.yml
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── routes.py
│   │   └── validators.py
│   ├── processor/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   └── data_processor.py
│   └── common/
│       ├── __init__.py
│       ├── config.py
│       ├── schemas.py
│       └── utils.py
├── tests/
│   ├── test_api.py
│   └── test_processor.py
├── requirements.txt
└── README.md




----------- Starting the Service ----------

# Navigate to docker directory
cd docker

# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps


# Create the topic
docker exec -it kafka kafka-topics.sh \
    --create \
    --topic membership-requests \
    --bootstrap-server localhost:9092 \
    --partitions 3 \
    --replication-factor 1

# Verify topic creation
docker exec -it kafka kafka-topics.sh \
    --describe \
    --topic membership-requests \
    --bootstrap-server localhost:9092


# In a new terminal
source venv/bin/activate
python src/api/main.py



# In another terminal
source venv/bin/activate
python src/processor/main.py

{
    "memberships": [
        {
            "ID": 1,
            "FirstName": "John",
            "LastName": "Doe",
            "BirthDate": "1990-01-01"
        },
        {
            "ID": 2,
            "FirstName": "Jane",
            "LastName": "Smith",
            "BirthDate": "1985-05-15"
        }
    ]
}


# Send file for processing
curl -X POST -F "file=@test_data.json" http://localhost:5000/api/v1/process

# You'll receive a response like:
{
    "message": "Processing started",
    "request_id": "123e4567-e89b-12d3-a456-426614174000",
    "status_endpoint": "/api/v1/status/123e4567-e89b-12d3-a456-426614174000"
}

# Check processing status
curl http://localhost:5000/api/v1/status/123e4567-e89b-12d3-a456-426614174000



# View messages in the topic
docker exec -it kafka kafka-console-consumer.sh \
    --bootstrap-server localhost:9092 \
    --topic membership-requests \
    --from-beginning


# Access Redis CLI
docker exec -it redis redis-cli

# View all keys
KEYS *

# View processing status for a request
HGETALL "request:123e4567-e89b-12d3-a456-426614174000"

# View processed results
LRANGE "results:123e4567-e89b-12d3-a456-426614174000" 0 -1




# View API logs
docker logs -f api

# View processor logs
docker logs -f processor