from flask import Flask, request, jsonify
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
import logging
from datetime import datetime
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def create_spark_session() -> SparkSession:
    """Initialize and return a Spark session with optimized configurations"""
    try:
        spark = SparkSession.builder \
            .appName("RAF Calculator") \
            .config("spark.driver.memory", "4g") \
            .config("spark.executor.memory", "4g") \
            .config("spark.driver.maxResultSize", "2g") \
            .config("spark.sql.shuffle.partitions", "10") \
            .config("spark.default.parallelism", "10") \
            .config("spark.memory.offHeap.enabled", "true") \
            .config("spark.memory.offHeap.size", "2g") \
            .config("spark.sql.adaptive.enabled", "true") \
            .getOrCreate()
        
        # Set log level
        spark.sparkContext.setLogLevel("ERROR")
        
        logger.info("Spark session created successfully")
        return spark
    except Exception as e:
        logger.error(f"Failed to create Spark session: {str(e)}")
        raise

# Initialize Spark Session
spark = create_spark_session()

def process_dataframe(df):
    """Process data using PySpark with optimized operations"""
    try:
        logger.debug("Starting dataframe processing")
        start_time = time.time()
        
        # Repartition for better performance
        df = df.repartition(10)
        
        result = df \
            .withColumn("current_date", current_date()) \
            .withColumn("Age", year(col("current_date")) - year(col("BirthDate"))) \
            .withColumn("RiskScore", col("Age") * lit(0.1))
        
        # Cache the result
        result.cache()
        
        processing_time = time.time() - start_time
        logger.info(f"DataFrame processing completed in {processing_time:.2f} seconds")
        
        return result
    except Exception as e:
        logger.error(f"Error in process_dataframe: {str(e)}")
        raise

@app.route('/process_data', methods=['POST'])
def process_data():
    start_time = time.time()
    
    try:
        data = request.json
        if not data or 'memberships' not in data:
            return jsonify({'error': 'No data provided'}), 400

        # Process in smaller batches if data is large
        batch_size = 1000
        memberships = data['memberships']
        all_results = []
        
        for i in range(0, len(memberships), batch_size):
            batch = memberships[i:i + batch_size]
            
            # Create DataFrame for batch
            df = spark.createDataFrame(batch)
            df = df \
                .withColumn("BirthDate", to_date(col("BirthDate"))) \
                .withColumn("Name", concat(col("FirstName"), lit(" "), col("LastName")))
            
            result_df = process_dataframe(df)
            
            # Convert to Python objects
            batch_results = result_df.select(
                "ID", "Name", "BirthDate", "Age", "RiskScore"
            ).collect()
            
            all_results.extend([{
                'ID': row['ID'],
                'Name': row['Name'],
                'BirthDate': str(row['BirthDate']),
                'Age': row['Age'],
                'RiskScore': float(row['RiskScore'])
            } for row in batch_results])

        total_time = time.time() - start_time
        
        return jsonify({
            'message': 'Success',
            'count': len(all_results),
            'results': all_results,
            'execution_time': f"{total_time:.2f} seconds"
        })

    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5011, debug=False)