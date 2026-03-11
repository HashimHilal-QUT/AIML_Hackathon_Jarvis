from flask import Flask, request, jsonify
import pymssql
from datetime import datetime
import logging
from typing import List, Dict
from sqlalchemy import create_engine, text
import pandas as pd
import urllib.parse
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Database configuration
DB_CONFIG = {
    'server': '10.10.1.4',
    'database': 'HTTEST',
    'user': 'karol_bhandari',
    'password': 'karolbhandari@2024',
    'charset': 'UTF-8'
}

def get_db_connection():
    """Establish a connection to the database."""
    return pymssql.connect(
        server=DB_CONFIG['server'],
        database=DB_CONFIG['database'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        charset=DB_CONFIG['charset']
    )

@app.route('/')
def home():
    """API documentation endpoint."""
    return """
    <h1>RAF Calculator API</h1>
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
    """

@app.route('/process_data', methods=['POST'])
def process_data():
    try:
        # Get input data
        data = request.json
        if not data or 'memberships' not in data:
            return jsonify({'error': 'No memberships data provided'}), 400
            
        memberships = data['memberships']
        print("Processing memberships:")

        # Get database connection
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Create temporary table
            cursor.execute("""
                IF OBJECT_ID('tempdb..#TempInputData') IS NOT NULL
                    DROP TABLE #TempInputData;
                
                CREATE TABLE #TempInputData (
                    ID INT,
                    FirstName NVARCHAR(100),
                    LastName NVARCHAR(100),
                    BirthDate DATE
                );
            """)

            # Insert data into temporary table
            for member in memberships:
                cursor.execute("""
                    INSERT INTO #TempInputData (ID, FirstName, LastName, BirthDate)
                    VALUES (%s, %s, %s, %s)
                """, (
                    int(''.join(filter(str.isdigit, str(member['ID'])))),
                    member['FirstName'],
                    member['LastName'],
                    datetime.strptime(member['BirthDate'], '%Y-%m-%d').date()
                ))

            # Execute the stored procedure with table variable
            cursor.execute("""
                DECLARE @MembershipTable MyMembershipType;
                
                INSERT INTO @MembershipTable (ID, Name, BirthDate)
                SELECT 
                    ID,
                    FirstName + ' ' + LastName,
                    BirthDate
                FROM #TempInputData;
                
                EXEC dbo.RAFCalculator @Memberships = @MembershipTable;
                
                DROP TABLE #TempInputData;
            """)

            # Process results
            results = []
            for row in cursor.fetchall():
                results.append({
                    'ID': row[0],
                    'Name': row[1],
                    'BirthDate': row[2].isoformat() if row[2] else None,
                    'Age': row[3] if row[3] is not None else None,
                    'RiskScore': float(row[4]) if row[4] is not None else None
                })

            conn.commit()
            
            return jsonify({
                'message': 'Data processed successfully',
                'count': len(results),
                'results': results
            })

        except Exception as e:
            conn.rollback()
            raise e

        finally:
            cursor.close()
            conn.close()

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

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5004)