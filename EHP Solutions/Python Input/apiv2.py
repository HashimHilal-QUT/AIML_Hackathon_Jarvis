from flask import Flask, request, jsonify
import pyodbc
from datetime import datetime, date
import json

app = Flask(__name__)

# Connection string for the destination database
destination_conn_str = (
    r'DRIVER={SQL Server};'
    r'SERVER=10.10.1.4;'
    r'DATABASE=HTTEST;'
    r'UID=karol_bhandari;'
    r'PWD=karolbhandari@2024;'
)

def get_table_type_info(cursor, type_name):
    query = """
    SELECT c.name, t.name as data_type, c.max_length, c.precision, c.scale
    FROM sys.table_types tt
    JOIN sys.columns c ON c.object_id = tt.type_table_object_id
    JOIN sys.types t ON t.user_type_id = c.user_type_id
    WHERE tt.name = ?
    ORDER BY c.column_id
    """
    cursor.execute(query, type_name)
    result = cursor.fetchall()
    print("Table type structure:", result)  # Debugging: print table type structure
    return result

def to_string(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value) if value is not None else ''


@app.route('/', methods=['GET'])
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>RAF Calculator API</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                line-height: 1.6;
            }
            .endpoint {
                background-color: #f4f4f4;
                padding: 15px;
                border-radius: 5px;
                margin: 10px 0;
            }
            code {
                background-color: #e8e8e8;
                padding: 2px 5px;
                border-radius: 3px;
            }
        </style>
    </head>
    <body>
        <h1>RAF Calculator API Documentation</h1>
        <p>Welcome to the RAF Calculator API. This API provides endpoints for processing membership data.</p>
        
        <div class="endpoint">
            <h2>Process Data Endpoint</h2>
            <p><strong>URL:</strong> <code>/process_data</code></p>
            <p><strong>Method:</strong> POST</p>
            <p><strong>Description:</strong> Process membership data and calculate RAF values.</p>
            
            <h3>Request Format:</h3>
            <pre><code>
{
    "memberships": [
        {
            "ID": "string",
            "FirstName": "string",
            "LastName": "string",
            "BirthDate": "YYYY-MM-DD"
        }
    ]
}
            </code></pre>
            
            <h3>Response Format:</h3>
            <pre><code>
{
    "message": "Data processed successfully",
    "results": [
        // Processed results array
    ]
}
            </code></pre>
        </div>
        
        <footer>
            <p>For more information, contact support.</p>
        </footer>
    </body>
    </html>
    '''

@app.route('/process_data', methods=['POST'])
def process_data():
    try:
        # Add request data logging
        print("Received request data:", request.get_data())
        
        # Get input data
        data = request.json
        if not data or 'memberships' not in data:
            return jsonify({'error': 'No memberships data provided'}), 400
            
        memberships = data['memberships']
        print("Processing memberships:", memberships)

        # Connect to the destination database
        try:
            conn = pyodbc.connect(destination_conn_str)
            cursor = conn.cursor()
        except pyodbc.Error as e:
            print("Database connection error:", str(e))
            return jsonify({'error': f'Database connection failed: {str(e)}'}), 500

        # Get table type info with error handling
        try:
            type_name = 'MyMembershipType'
            type_info = get_table_type_info(cursor, type_name)
            if not type_info:
                return jsonify({'error': f'Table type {type_name} not found'}), 500
            print("Type info retrieved:", type_info)
        except Exception as e:
            print("Error getting table type info:", str(e))
            return jsonify({'error': f'Failed to get table type info: {str(e)}'}), 500

        columns = ', '.join([col[0] for col in type_info])
        print("Columns:", columns)

        # Execute the SQL for each membership
        all_results = []
        for member in memberships:
            try:
                # Validate required fields
                required_fields = ['ID', 'FirstName', 'LastName', 'BirthDate']
                if not all(field in member for field in required_fields):
                    missing_fields = [field for field in required_fields if field not in member]
                    raise ValueError(f"Missing required fields: {missing_fields}")

                # Convert ID to integer by extracting numeric part
                id_str = member['ID']
                if isinstance(id_str, str):
                    numeric_id = ''.join(filter(str.isdigit, id_str))
                    member_id = int(numeric_id) if numeric_id else 0
                else:
                    member_id = int(id_str)

                # Create name with SQL injection prevention
                name = f"{member['FirstName']} {member['LastName']}"
                name = name.replace("'", "''")  # Escape single quotes
                
                # Convert and validate birth date
                birth_date = member['BirthDate']
                if isinstance(birth_date, str):
                    try:
                        birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
                    except ValueError as e:
                        raise ValueError(f"Invalid birth date format for member {member_id}: {str(e)}")

                print(f"Processing member: ID={member_id}, Name={name}, BirthDate={birth_date}")

                # SQL query with parameters
                sql = f"""
                DECLARE @TempMemberships MyMembershipType;
                DECLARE @Results NVARCHAR(MAX);

                INSERT INTO @TempMemberships ({columns})
                VALUES ({member_id}, N'{name}', '{birth_date}', 1);
                
                EXEC dbo.RAFCalculatorJson @Memberships=@TempMemberships, @Results=@Results OUTPUT;

                SELECT @Results AS Results;
                """
                print("Executing SQL:", sql)

                cursor.execute(sql)
                cursor.nextset()
                result = cursor.fetchone()
                
                if result and result.Results:
                    parsed_results = json.loads(result.Results)
                    all_results.extend(parsed_results if isinstance(parsed_results, list) else [parsed_results])
                    print(f"Processed member {member_id} successfully")
                else:
                    print(f"No results returned for member {member_id}")

            except Exception as e:
                print(f"Error processing member {id_str}: {str(e)}")
                return jsonify({'error': f'Error processing member {id_str}: {str(e)}'}), 500

        conn.commit()
        conn.close()

        return jsonify({
            'message': 'Data processed successfully',
            'count': len(all_results),
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
# Batch processing
# @app.route('/process_data', methods=['POST'])
# def process_data():
#     try:
#         data = request.json
#         memberships = data['memberships']
#         conn = pyodbc.connect(destination_conn_str)
#         cursor = conn.cursor()
#         type_name = 'MyMembershipType'
#         type_info = get_table_type_info(cursor, type_name)

#         columns = ', '.join([col.name for col in type_info])
#         placeholders = ', '.join(['(?, ?, ?, ?)'])  # Assuming 4 columns in MyMembershipType

#         sql = f"""
#         DECLARE @TempMemberships MyMembershipType;
#         DECLARE @Results NVARCHAR(MAX);

#         INSERT INTO @TempMemberships ({columns})
#         VALUES {placeholders};
        
#         EXEC dbo.RAFCalculatorJson @Memberships=@TempMemberships, @Results=@Results OUTPUT;

#         SELECT @Results AS Results;
#         """

#         all_results = []
#         batch_size = 100  # Adjust this based on your system's capabilities
#         for i in range(0, len(memberships), batch_size):
#             batch = memberships[i:i+batch_size]
#             batch_values = []
#             for member in batch:
#                 name = f"{member['FirstName']} {member['LastName']}"
#                 batch_values.extend([member['ID'], name, member['BirthDate'], 1])
            
#             # Adjust the SQL query for the current batch size
#             batch_placeholders = ', '.join(['(?, ?, ?, ?)' for _ in range(len(batch))])
#             batch_sql = sql.replace(placeholders, batch_placeholders)
            
#             cursor.execute(batch_sql, batch_values)
#             cursor.nextset()
#             result = cursor.fetchone()
#             if result and result.Results:
#                 all_results.extend(json.loads(result.Results))

#         conn.commit()
#         conn.close()

#         return jsonify({
#             'message': 'Data processed successfully',
#             'results': all_results
#         })

#     except Exception as e:
#         return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)