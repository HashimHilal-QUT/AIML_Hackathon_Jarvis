from flask import Blueprint, request, jsonify
import uuid
from kafka import KafkaProducer
import json
import pandas as pd
from io import StringIO

api_bp = Blueprint('api', __name__)

# Initialize Kafka producer
producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

@api_bp.route('/api/v1/process', methods=['POST'])
def process_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Generate a unique request ID
    request_id = str(uuid.uuid4())
    
    try:
        # Read the CSV file
        content = file.read().decode('utf-8')
        df = pd.read_csv(StringIO(content))
        
        # Convert DataFrame to dictionary
        data = {
            'request_id': request_id,
            'data': df.to_dict(orient='records')
        }
        
        # Send to Kafka topic
        producer.send('health_data_topic', value=data)
        producer.flush()
        
        return jsonify({
            'error': None,
            'request_id': request_id,
            'message': 'File received and processing started',
            'status': 'processing'
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': 'Error processing file'
        }), 500

@api_bp.route('/api/v1/status/<request_id>', methods=['GET'])
def get_status(request_id):
    try:
        # Here you would typically check Redis or your database for the status
        # This is a placeholder implementation
        return jsonify({
            'request_id': request_id,
            'status': 'processing',  # or 'completed' or 'failed' based on actual status
            'error': None
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': 'Error checking status'
        }), 500