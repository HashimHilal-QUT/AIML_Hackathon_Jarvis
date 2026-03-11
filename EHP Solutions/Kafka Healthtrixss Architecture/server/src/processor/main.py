from kafka import KafkaConsumer
import json
from src.common.config import Config
from src.processor.data_processor import process_record
from src.common.utils import get_redis_connection
from datetime import datetime

def start_processor():
    consumer = KafkaConsumer(
        'membership-requests',
        bootstrap_servers=Config.KAFKA_BOOTSTRAP_SERVERS,
        group_id='membership-processor',
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        key_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        enable_auto_commit=False,
    )
    
    redis_conn = get_redis_connection()
    
    print("Starting processor service...")
    
    try:
        for message in consumer:
            try:
                # Process the record
                request_id = message.key
                result = process_record(message.value['data'])
                
                # Update Redis status
                redis_conn.hincrby(f"request:{request_id}", 'processed_records', 1)
                
                # Store processed result
                redis_conn.rpush(
                    f"results:{request_id}",
                    json.dumps(result)
                )
                
                # Check if processing is complete
                status = redis_conn.hgetall(f"request:{request_id}")
                if int(status['processed_records']) >= int(status['total_records']):
                    redis_conn.hset(
                        f"request:{request_id}",
                        mapping={
                            'status': 'COMPLETED',
                            'end_time': datetime.utcnow().isoformat()
                        }
                    )
                
                # Commit offset
                consumer.commit()
                
            except Exception as e:
                print(f"Error processing message: {str(e)}")
                # Implement error handling strategy here
                
    except KeyboardInterrupt:
        print("\nShutting down processor...")
    finally:
        consumer.close()

if __name__ == '__main__':
    start_processor()