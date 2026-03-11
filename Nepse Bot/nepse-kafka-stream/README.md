# NEPSE Market Data Streaming with Kafka

This project implements a real-time market data streaming system for Nepal Stock Exchange (NEPSE) using Apache Kafka.

## Architecture

- **Producer**: Fetches market data from merolagani.com and publishes to Kafka topics
- **Kafka**: Message broker handling the streaming data
- **Consumer**: Processes the market data streams

## Setup

1. Install Docker and Docker Compose
2. Clone this repository
3. Run the system:
   ```bash
   docker-compose up --build
   ```

## Components

- `market_producer.py`: Fetches and publishes market data
- `market_consumer.py`: Consumes and processes market data
- Docker configuration for containerization
- Kafka and Zookeeper services

## Configuration

- Default refresh interval: 60 seconds
- Default monitored symbol: HRL
- Kafka topics format: nepse.market.<symbol>

## Extending

You can extend the consumer to:
- Save data to a database
- Generate alerts
- Create real-time analytics
- Feed data to a dashboard

## Monitoring

- Producer logs show successful data fetching and publishing
- Consumer logs show received messages
- Kafka topics can be monitored using standard Kafka tools

## Notes

- Handle API rate limits appropriately
- Monitor system resources
- Implement error handling as needed
