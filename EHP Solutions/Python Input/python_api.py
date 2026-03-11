from flask import Flask, request, jsonify
import pandas as pd
import json
from datetime import datetime
import time
from typing import Dict, List

app = Flask(__name__)

def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Replicate the stored procedure logic using pandas"""
    # Calculate Age and RiskScore
    current_date = pd.Timestamp.now()
    df['Age'] = (current_date - pd.to_datetime(df['BirthDate'])).dt.days // 365
    df['RiskScore'] = df['Age'] * 0.1
    
    return df

@app.route('/process_data', methods=['POST'])
def process_data():
    try:
        # Get JSON data from request
        data = request.json
        if not data or 'memberships' not in data:
            return jsonify({'error': 'No memberships data provided'}), 400

        # Convert to DataFrame
        df = pd.DataFrame(data['memberships'])
        
        # Convert data types
        df['BirthDate'] = pd.to_datetime(df['BirthDate'])
        df['ID'] = df['ID'].astype(int)
        df['FirstName'] = df['FirstName'].astype(str)
        df['LastName'] = df['LastName'].astype(str)
        
        # Add Name column
        df['Name'] = df['FirstName'] + ' ' + df['LastName']
        
        # Process the data
        result_df = process_dataframe(df)
        
        # Convert to desired output format
        results = result_df.apply(lambda x: {
            'ID': int(x['ID']),
            'Name': x['Name'],
            'BirthDate': x['BirthDate'].strftime('%Y-%m-%d'),
            'Age': int(x['Age']),
            'RiskScore': float(x['RiskScore'])
        }, axis=1).tolist()

        return jsonify({
            'message': 'Data processed successfully',
            'count': len(results),
            'results': results,
            'invalid_members': []
        })

    except Exception as e:
        return jsonify({
            'error': str(e),
            'error_type': type(e).__name__
        }), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)