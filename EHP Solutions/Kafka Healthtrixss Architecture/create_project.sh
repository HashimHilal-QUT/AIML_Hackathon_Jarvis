#!/bin/bash

# Create main project directory
mkdir -p server

# Create directory structure
cd server
mkdir -p docker src/api src/processor src/common tests

# Create docker files
cat > docker/Dockerfile.api << 'EOF'
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ /app/src/

CMD ["python", "-m", "src.api.main"]
EOF

cat > docker/Dockerfile.processor << 'EOF'
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ /app/src/

CMD ["python", "-m", "src.processor.main"]
EOF

cat > docker/docker-compose.yml << 'EOF'
version: '3.8'

services:
  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    ports:
      - "2181:2181"

  kafka:
    image: confluentinc/cp-kafka:latest
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1

  redis:
    image: redis:latest
    ports:
      - "6379:6379"

  api:
    build:
      context: ..
      dockerfile: docker/Dockerfile.api
    ports:
      - "5000:5000"
    depends_on:
      - kafka
      - redis

  processor:
    build:
      context: ..
      dockerfile: docker/Dockerfile.processor
    depends_on:
      - kafka
      - redis
EOF

# Create source files
# API
touch src/api/__init__.py

cat > src/api/main.py << 'EOF'
from flask import Flask
from flask_cors import CORS
from src.common.config import Config
from src.api.routes import api_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    CORS(app)
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000)
EOF

cat > src/api/routes.py << 'EOF'
from flask import Blueprint, request, jsonify
from kafka import KafkaProducer
import json
import uuid
from src.common.validators import validate_json_file
from src.common.utils import get_redis_connection

api_bp = Blueprint('api', __name__)

# Add your route handlers here
EOF

cat > src/api/validators.py << 'EOF'
from typing import Union
from werkzeug.datastructures import FileStorage

def validate_json_file(file: FileStorage) -> Union[bool, str]:
    """Validate uploaded JSON file"""
    if not file or file.filename == '':
        return "No file provided"
    
    if not file.filename.endswith('.json'):
        return "File must be JSON format"
        
    return True
EOF

# Processor
touch src/processor/__init__.py

cat > src/processor/main.py << 'EOF'
from kafka import KafkaConsumer
import json
from src.common.config import Config
from src.processor.data_processor import process_record
from src.common.utils import get_redis_connection

def start_processor():
    consumer = KafkaConsumer(
        'membership-requests',
        bootstrap_servers=Config.KAFKA_BOOTSTRAP_SERVERS,
        group_id='membership-processor',
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    
    for message in consumer:
        process_record(message.value)

if __name__ == '__main__':
    start_processor()
EOF

cat > src/processor/data_processor.py << 'EOF'
from typing import Dict, Any
import pandas as pd
from datetime import datetime

def process_record(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single record"""
    # Add your processing logic here
    return data
EOF

# Common
touch src/common/__init__.py

cat > src/common/config.py << 'EOF'
import os

class Config:
    KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:29092')
    REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
EOF

cat > src/common/schemas.py << 'EOF'
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class MembershipRecord:
    id: int
    first_name: str
    last_name: str
    birth_date: datetime
EOF

cat > src/common/utils.py << 'EOF'
import redis
from src.common.config import Config

def get_redis_connection():
    return redis.Redis(
        host=Config.REDIS_HOST,
        port=Config.REDIS_PORT,
        decode_responses=True
    )
EOF

# Tests
cat > tests/test_api.py << 'EOF'
import pytest
from src.api.main import create_app

@pytest.fixture
def app():
    app = create_app()
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_process_endpoint(client):
    # Add your API tests here
    pass
EOF

cat > tests/test_processor.py << 'EOF'
import pytest
from src.processor.data_processor import process_record

def test_process_record():
    # Add your processor tests here
    pass
EOF

# Requirements file
cat > requirements.txt << 'EOF'
flask==2.0.1
flask-cors==3.0.10
kafka-python==2.0.2
redis==4.3.4
pandas==1.4.2
pytest==7.1.1
requests==2.27.1
EOF

# README
cat > README.md << 'EOF'
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
EOF

# Make the script executable
chmod +x create_project.sh