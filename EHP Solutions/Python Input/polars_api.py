from flask import Flask, request, jsonify
import polars as pl
from datetime import datetime
from typing import Dict, List

app = Flask(__name__)

def process_dataframe(df: pl.DataFrame) -> pl.DataFrame:
    """Replicate the stored procedure logic using polars"""
    return df.with_columns([
        # Calculate age using year difference
        ((pl.col('current_date').dt.year() - pl.col('BirthDate').dt.year())).alias('Age')
    ]).with_columns([
        # Calculate risk score
        (pl.col('Age') * 0.1).alias('RiskScore')
    ])

@app.route('/process_data', methods=['POST'])
def process_data():
    try:
        # Get JSON data from request
        data = request.json
        if not data or 'memberships' not in data:
            return jsonify({'error': 'No memberships data provided'}), 400

        # Convert to Polars DataFrame
        df = pl.DataFrame(data['memberships'])
        
        # Add current_date column for age calculation
        df = df.with_columns(pl.lit(datetime.now()).alias('current_date'))
        
        # Convert data types
        df = df.with_columns([
            pl.col('BirthDate').str.strptime(pl.Date, format='%Y-%m-%d'),
            pl.col('ID').cast(pl.Int64),
            pl.col('FirstName').cast(pl.Utf8),
            pl.col('LastName').cast(pl.Utf8)
        ])
        
        # Add Name column
        df = df.with_columns([
            (pl.col('FirstName') + ' ' + pl.col('LastName')).alias('Name')
        ])
        
        # Process the data
        result_df = process_dataframe(df)
        
        # Convert to desired output format
        results = result_df.select([
            pl.col('ID'),
            pl.col('Name'),
            pl.col('BirthDate').cast(str),
            pl.col('Age'),
            pl.col('RiskScore')
        ]).to_dicts()
        
        # Format the results to match the expected structure
        formatted_results = [{
            'ID': int(r['ID']),
            'Name': r['Name'],
            'BirthDate': r['BirthDate'],
            'Age': int(r['Age']),
            'RiskScore': float(r['RiskScore'])
        } for r in results]

        return jsonify({
            'message': 'Data processed successfully',
            'count': len(formatted_results),
            'results': formatted_results,
            'invalid_members': []
        })

    except Exception as e:
        return jsonify({
            'error': str(e),
            'error_type': type(e).__name__
        }), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)