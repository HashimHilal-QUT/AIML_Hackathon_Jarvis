from kafka import KafkaConsumer, KafkaProducer
from flask import Flask, request, jsonify
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import json
import logging
from datetime import datetime
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Kafka Configuration
KAFKA_INPUT_TOPIC = 'membership_input'
KAFKA_OUTPUT_TOPIC = 'membership_output'
KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'

# Initialize Kafka producer for results
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def create_spark_session() -> SparkSession:
    """Initialize Spark session with Kafka integration"""
    try:
        spark = SparkSession.builder \
            .appName("RAF Calculator Streaming") \
            .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.2.0") \
            .config("spark.streaming.kafka.maxRatePerPartition", "100") \
            .config("spark.driver.memory", "4g") \
            .config("spark.executor.memory", "4g") \
            .getOrCreate()
        
        spark.sparkContext.setLogLevel("ERROR")
        return spark
    except Exception as e:
        logger.error(f"Failed to create Spark session: {str(e)}")
        raise

# Define schema for incoming data
membership_schema = StructType([
    StructField("ID", StringType(), True),
    StructField("FirstName", StringType(), True),
    StructField("LastName", StringType(), True),
    StructField("BirthDate", StringType(), True)
])

def process_streaming_data():
    """Process streaming data from Kafka"""
    try:
        # Create streaming DataFrame from Kafka
        df_stream = spark \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
            .option("subscribe", KAFKA_INPUT_TOPIC) \
            .load()

        # Parse JSON data
        parsed_df = df_stream.select(
            from_json(
                col("value").cast("string"),
                membership_schema
            ).alias("data")
        ).select("data.*")

        # Process data
        result = parsed_df \
            .withColumn("BirthDate", to_date(col("BirthDate"))) \
            .withColumn("Name", concat(col("FirstName"), lit(" "), col("LastName"))) \
            .withColumn("current_date", current_date()) \
            .withColumn("Age", year(col("current_date")) - year(col("BirthDate"))) \
            .withColumn("RiskScore", col("Age") * lit(0.1))

        # Write results back to Kafka
        query = result \
            .selectExpr("to_json(struct(*)) AS value") \
            .writeStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
            .option("topic", KAFKA_OUTPUT_TOPIC) \
            .option("checkpointLocation", "/tmp/checkpoint") \
            .start()

        return query

    except Exception as e:
        logger.error(f"Error in stream processing: {str(e)}")
        raise

@app.route('/submit_data', methods=['POST'])
def submit_data():
    """API endpoint to submit data to Kafka"""
    try:
        data = request.json
        if not data or 'memberships' not in data:
            return jsonify({'error': 'No data provided'}), 400

        # Send each membership record to Kafka
        for membership in data['memberships']:
            producer.send(KAFKA_INPUT_TOPIC, membership)
        
        producer.flush()
        
        return jsonify({
            'message': 'Data submitted successfully to processing queue',
            'count': len(data['memberships'])
        })

    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/consume_messages', methods=['GET'])
def consume_messages():
    """API endpoint to consume messages from Kafka"""
    try:
        # Create a consumer instance
        consumer = KafkaConsumer(
            KAFKA_OUTPUT_TOPIC,
            bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            auto_offset_reset='earliest',  # Start from earliest message
            consumer_timeout_ms=1000  # Timeout after 1 second if no message
        )

        # Collect messages
        messages = []
        for message in consumer:
            messages.append(message.value)
        
        # Close the consumer
        consumer.close()

        return jsonify({
            'message_count': len(messages),
            'messages': messages
        })

    except Exception as e:
        logger.error(f"Error consuming messages: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Initialize Spark Session and start streaming
spark = create_spark_session()
streaming_query = process_streaming_data()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5011, debug=False)