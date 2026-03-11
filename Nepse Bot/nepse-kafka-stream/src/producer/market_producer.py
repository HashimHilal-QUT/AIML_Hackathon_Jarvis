import json
import time
import logging
import requests
from kafka import KafkaProducer
from json import dumps
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketDataProducer:
    def __init__(self, bootstrap_servers=['kafka:9092']):
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda x: dumps(x).encode('utf-8'),
            api_version=(0, 10, 1)
        )
        self.api_url = "https://merolagani.com/handlers/webrequesthandler.ashx?type=market_summary"

    def fetch_market_data(self):
        try:
            response = requests.get(self.api_url)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to fetch data: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error fetching market data: {str(e)}")
            return None

    def process_and_send(self, market_data):
        if not market_data or 'turnover' not in market_data:
            return

        details = market_data.get('turnover', {}).get('detail', [])
        
        for stock in details:
            try:
                # Add timestamp to the data
                stock['timestamp'] = datetime.now().isoformat()
                
                # Send to Kafka topic based on symbol
                symbol = stock.get('s', 'unknown')
                self.producer.send(f'nepse.market.{symbol}', value=stock)
                logger.info(f"Sent data for symbol: {symbol}")
            except Exception as e:
                logger.error(f"Error sending data for symbol {symbol}: {str(e)}")

    def run(self, interval_seconds=60):
        while True:
            market_data = self.fetch_market_data()
            if market_data:
                self.process_and_send(market_data)
            time.sleep(interval_seconds)

if __name__ == "__main__":
    producer = MarketDataProducer()
    producer.run()
