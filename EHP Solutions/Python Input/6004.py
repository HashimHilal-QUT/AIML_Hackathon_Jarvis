from flask import Flask, request, jsonify
import pymssql
from datetime import datetime
import logging
from typing import List, Dict
from sqlalchemy import create_engine, text
import pandas as pd
import urllib.parse
import json
import time
import os
from tqdm import tqdm
from sqlalchemy.ext.declarative import declarative_base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
Base = declarative_base()

# Constants
BATCH_SIZE = 5000  # Adjust based on your server's capacity

# Database configuration
DB_CONFIG = {
    'server': '10.10.1.4',
    'database': 'HTTEST',
    'user': 'karol_bhandari',
    'password': 'karolbhandari@2024',
    'charset': 'UTF-8'
}

def custom_to_sql(df, table_name, engine, chunksize=10000):
    """Custom implementation of to_sql with progress bar"""
    total_rows = len(df)
    with tqdm(total=total_rows, desc="Inserting data") as pbar:
        for i in range(0, total_rows, chunksize):
            chunk = df[i:i + chunksize]
            chunk.to_sql(
                table_name,
                engine,
                if_exists='append' if i > 0 else 'replace',
                index=False,
                method='multi'
            )
            pbar.update(len(chunk))
@app.get("/")
def root():
    return {
        "message": "RAF Calculator API",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }

@app.route('/')
def home():
    """API documentation endpoint."""
    return """
    <h1>RAF Calculator API (Bulk Insert SQLAlchemy)</h1>
    <p>POST /process_data with JSON payload:</p>
    <pre>
    {
        "memberships": [
            {
                "ID": "12345",
                "FirstName": "John",
                "LastName": "Doe",
                "BirthDate": "1990-01-01"
            }
        ]
    }
    </pre>
    <p>This endpoint uses Polars for efficient data processing.</p>
    """

@app.route('/process_data', methods=['POST'])
def process_data():
    total_start_time = time.time()
    try:
        # Get input data
        data = request.json
        if not data or 'memberships' not in data:
            return jsonify({'error': 'No memberships data provided'}), 400
            
        # Convert to DataFrame
        df_start_time = time.time()
        print("Converting to DataFrame...")
        df = pd.DataFrame(data['memberships'])
        
        # Convert and validate data types
        print("Converting dates...")
        df['BirthDate'] = pd.to_datetime(df['BirthDate'])
        df['ID'] = df['ID'].astype(int)
        df['FirstName'] = df['FirstName'].astype(str)
        df['LastName'] = df['LastName'].astype(str)
        df['BirthDate'] = pd.to_datetime(df['BirthDate'])
        df_end_time = time.time()
        print(f"DataFrame conversion completed in {df_end_time - df_start_time:.2f} seconds")
        
        print("\nDataFrame preview:")
        print(df.head())
        print(f"Total records to be processed: {len(df):,}")
        
        # Create connection string
        db_start_time = time.time()
        print("\nCreating database connection...")
        params = urllib.parse.quote_plus(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            'SERVER=10.10.1.4;'
            'DATABASE=HTTEST;'
            'UID=karol_bhandari;'
            'PWD=karolbhandari@2024;'
            'TrustServerCertificate=yes;'
        )
        
        engine = create_engine(
            f'mssql+pyodbc:///?odbc_connect={params}',
            fast_executemany=True
        )
        
        all_results = []
        
        with engine.connect() as connection:
            # Process in batches
            for start_idx in range(0, len(df), BATCH_SIZE):
                batch_df = df.iloc[start_idx:start_idx + BATCH_SIZE]
                
                # Create temporary table for this batch
                print(f"\nProcessing batch {start_idx//BATCH_SIZE + 1} of {(len(df) + BATCH_SIZE - 1)//BATCH_SIZE}")
                connection.execute(text("""
                    IF OBJECT_ID('tempdb..#TempBatch') IS NOT NULL
                        DROP TABLE #TempBatch;
                    
                    CREATE TABLE #TempBatch (
                        ID INT,
                        FirstName NVARCHAR(100),
                        LastName NVARCHAR(100),
                        BirthDate DATE
                    );
                """))
                
                # Bulk insert batch data
                batch_df.to_sql('#TempBatch', connection, if_exists='append', index=False, method='multi')
                
                # Process batch with stored procedure
                result = connection.execute(text("""
                    DECLARE @MembershipTable MyMembershipType;
                    
                    INSERT INTO @MembershipTable (ID, Name, BirthDate)
                    SELECT 
                        ID,
                        FirstName + ' ' + LastName,
                        CAST(BirthDate as DATE)
                    FROM #TempBatch;
                    
                    EXEC dbo.RAFCalculator @Memberships = @MembershipTable;
                    
                    DROP TABLE #TempBatch;
                """))
                
                # Collect results
                batch_results = []
                for row in result:
                    batch_results.append({
                        'ID': row[0],
                        'Name': row[1],
                        'BirthDate': row[2].isoformat() if row[2] else None,
                        'Age': row[3] if row[3] is not None else None,
                        'RiskScore': float(row[4]) if row[4] is not None else None
                    })
                
                all_results.extend(batch_results)
                print(f"Processed {len(all_results):,} records so far")
        
        db_end_time = time.time()
        total_time = db_end_time - db_start_time
        print(f"\nDatabase operations completed in {total_time:.2f} seconds")
        print(f"Average speed: {len(df)/total_time:,.2f} records/second")
        
        return jsonify({
            'message': 'Data processed successfully',
            'count': len(all_results),
            'processing_time_seconds': time.time() - total_start_time,
            'records_per_second': len(df)/(time.time() - total_start_time),
            'results': all_results
        })

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback_str = traceback.format_exc()
        print(f"Traceback: {traceback_str}")
        return jsonify({
            'error': str(e),
            'error_type': type(e).__name__,
            'traceback': traceback_str
        }), 500

    finally:
        if 'engine' in locals():
            engine.dispose()
            print("\nDatabase connection closed.")

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 6004))
    app.run(host='0.0.0.0', port=port, debug=True, threaded=True)