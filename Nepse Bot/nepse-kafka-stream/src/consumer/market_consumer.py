import json
import logging
from kafka import KafkaConsumer
from json import loads

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketDataConsumer:
    def __init__(self, symbols=['HRL'], bootstrap_servers=['kafka:9092']):
        self.topics = [f'nepse.market.{symbol}' for symbol in symbols]
        self.consumer = KafkaConsumer(
            *self.topics,
            bootstrap_servers=bootstrap_servers,
            auto_offset_reset='latest',
            enable_auto_commit=True,
            group_id='nepse_market_group',
            value_deserializer=lambda x: loads(x.decode('utf-8')),
            api_version=(0, 10, 1)
        )

    def process_message(self, message):
        try:
            # Process the message here
            # You can add your custom processing logic
            symbol = message.topic.split('.')[-1]
            data = message.value
            logger.info(f"Received data for {symbol}: {data}")
            
            # Example: You could save to database, trigger alerts, etc.
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")

    def run(self):
        try:
            for message in self.consumer:
                self.process_message(message)
        except Exception as e:
            logger.error(f"Consumer error: {str(e)}")

if __name__ == "__main__":
    consumer = MarketDataConsumer()
    consumer.run()
