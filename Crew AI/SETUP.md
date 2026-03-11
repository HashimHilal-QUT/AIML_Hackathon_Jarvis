# 🚀 Setup Guide: AI-Powered Business Intelligence Platform

## Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose (for full deployment)
- OpenAI API key
- Git

## Quick Start (Local Development)

### 1. Clone and Setup Environment

```bash
# Clone the repository
git clone <your-repo-url>
cd crew-ai-business-intelligence

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your actual values
nano .env  # or use your preferred editor
```

**Required Environment Variables:**
```ini
# OpenAI Configuration (REQUIRED)
OPENAI_API_KEY=your_actual_openai_api_key_here
OPENAI_MODEL=gpt-4-turbo-preview

# Database Configuration
DATABASE_URL=sqlite:///data/market_intelligence.db
REDIS_URL=redis://localhost:6379

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

### 3. Initialize Data Storage

```bash
# Create necessary directories
mkdir -p data reports logs

# Initialize SQLite database (will be created automatically on first run)
python -c "from services.data_service import DataService; DataService()._initialize_storage()"
```

### 4. Run the Demo

```bash
# Run the comprehensive demo
python demo.py
```

This will showcase:
- Technology industry analysis
- Healthcare market research
- Financial services intelligence
- Retail competitive analysis
- Advanced features demonstration

## Full Deployment with Docker

### 1. Docker Setup

```bash
# Build and start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f app
```

### 2. Access the Application

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health
- **Main Application**: http://localhost:8000

### 3. API Endpoints

```bash
# Market Analysis
curl -X POST "http://localhost:8000/api/analyze-market" \
  -H "Content-Type: application/json" \
  -d '{
    "industry": "technology",
    "companies": ["Apple", "Microsoft", "Google"],
    "analysis_depth": "comprehensive"
  }'

# Start Continuous Monitoring
curl -X POST "http://localhost:8000/api/start-monitoring" \
  -H "Content-Type: application/json" \
  -d '{
    "industry": "technology",
    "monitoring_interval": 3600
  }'
```

## Development Workflow

### 1. Running Individual Components

```bash
# Run FastAPI server only
python main.py

# Run with hot reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run Celery worker (in separate terminal)
celery -A main.celery worker --loglevel=info

# Run Celery beat scheduler (in separate terminal)
celery -A main.celery beat --loglevel=info
```

### 2. Testing Individual Agents

```python
# Test data collector agent
python -c "
from agents.data_collector import DataCollectorAgent
from services.data_service import DataService
from langchain_openai import ChatOpenAI
import asyncio

async def test_data_collector():
    llm = ChatOpenAI(api_key='your_key')
    data_service = DataService()
    agent = DataCollectorAgent(llm, data_service)
    crew_agent = agent.create_agent()
    print('Data Collector Agent created successfully!')

asyncio.run(test_data_collector())
"
```

### 3. Custom Analysis Scenarios

```python
# Create custom analysis
from main import BusinessIntelligenceCrew
import asyncio

async def custom_analysis():
    crew = BusinessIntelligenceCrew()
    
    # Custom industry analysis
    result = await crew.run_market_analysis(
        industry="automotive",
        companies=["Tesla", "Ford", "GM"],
        analysis_depth="comprehensive"
    )
    
    print("Analysis completed:", result)

asyncio.run(custom_analysis())
```

## Monitoring and Logs

### 1. Application Logs

```bash
# View application logs
tail -f logs/app.log

# View specific service logs
docker-compose logs -f app
docker-compose logs -f worker
docker-compose logs -f scheduler
```

### 2. Database Monitoring

```bash
# SQLite database (local development)
sqlite3 data/market_intelligence.db

# PostgreSQL (Docker deployment)
docker-compose exec postgres psql -U crewai -d market_intelligence
```

### 3. Redis Monitoring

```bash
# Redis CLI
docker-compose exec redis redis-cli

# Monitor Redis operations
docker-compose exec redis redis-cli monitor
```

## Troubleshooting

### Common Issues

1. **OpenAI API Key Error**
   ```bash
   # Ensure your API key is set correctly
   echo $OPENAI_API_KEY
   # Should show your actual API key
   ```

2. **Database Connection Issues**
   ```bash
   # Check database status
   docker-compose ps postgres
   
   # Restart database service
   docker-compose restart postgres
   ```

3. **Redis Connection Issues**
   ```bash
   # Check Redis status
   docker-compose ps redis
   
   # Test Redis connection
   docker-compose exec redis redis-cli ping
   ```

4. **Port Conflicts**
   ```bash
   # Check if ports are in use
   lsof -i :8000
   lsof -i :6379
   lsof -i :5432
   
   # Kill processes if needed
   kill -9 <PID>
   ```

### Performance Optimization

1. **Increase Worker Processes**
   ```bash
   # Edit docker-compose.yml
   worker:
     command: celery -A main.celery worker --loglevel=info --concurrency=4
   ```

2. **Optimize Database**
   ```bash
   # Add database indexes
   docker-compose exec postgres psql -U crewai -d market_intelligence -c "
   CREATE INDEX idx_market_data_timestamp ON market_data(timestamp);
   CREATE INDEX idx_analysis_results_industry ON analysis_results(industry);
   "
   ```

3. **Redis Optimization**
   ```bash
   # Configure Redis for better performance
   # Edit docker-compose.yml redis service
   redis:
     command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
   ```

## Production Deployment

### 1. Environment Variables for Production

```bash
# Production .env
OPENAI_API_KEY=your_production_key
DATABASE_URL=postgresql://user:pass@prod-db:5432/market_intelligence
REDIS_URL=redis://prod-redis:6379
LOG_LEVEL=WARNING
ENVIRONMENT=production
```

### 2. Kubernetes Deployment

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods
kubectl get services
```

### 3. SSL/TLS Configuration

```bash
# Generate SSL certificates
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/nginx.key -out ssl/nginx.crt

# Update nginx.conf with SSL configuration
```

## LinkedIn Showcase Preparation

### 1. Record Demo Session

```bash
# Record terminal session
script demo-session.log
python demo.py
exit

# Or use asciinema for better quality
asciinema rec demo-session.cast
python demo.py
```

### 2. Generate Screenshots

```bash
# Take screenshots of key features
# - API documentation
# - Analysis results
# - Dashboard (if implemented)
# - Docker containers running
```

### 3. Prepare Metrics

```bash
# Collect performance metrics
python -c "
from services.data_service import DataService
ds = DataService()
stats = ds.get_data_statistics()
print('Data Statistics:', stats)
"
```

## Next Steps

1. **Customize Analysis**: Modify agents and tools for your specific use case
2. **Add Data Sources**: Integrate real APIs (Yahoo Finance, Alpha Vantage, etc.)
3. **Implement Dashboard**: Create a web-based dashboard for visualization
4. **Add Authentication**: Implement user authentication and authorization
5. **Scale Infrastructure**: Deploy to cloud providers (AWS, GCP, Azure)
6. **Add ML Models**: Integrate custom machine learning models for predictions

## Support

- **Documentation**: Check `README.md` for detailed project overview
- **LinkedIn Showcase**: See `linkedin_showcase.md` for presentation materials
- **Demo Script**: Run `python demo.py` for comprehensive demonstration
- **API Documentation**: Visit http://localhost:8000/docs when running

---

**Ready to showcase your master-level Crew AI skills! 🚀** 