from flask import Flask, request, jsonify
import pymssql
from datetime import datetime
import logging
import tempfile
import csv
import os
from tqdm import tqdm 

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

def create_temp_table(cursor):
    """Create a temporary table with the desired structure."""
    cursor.execute("""
    IF OBJECT_ID('tempdb..#TempMembers') IS NOT NULL
        DROP TABLE #TempMembers;

    CREATE TABLE #TempMembers (
        ID INT,
        Name NVARCHAR(100),
        BirthDate DATE
    );
    """)

def bulk_insert_from_memory(cursor, memberships):
    """Perform a bulk insert operation using a temporary CSV file."""
    temp_file = None
    try:
        # Create a temporary file in the current directory
        temp_file = tempfile.NamedTemporaryFile(mode='w', newline='', delete=False, suffix='.csv', dir=os.getcwd())

        # Write data to the temporary CSV file
        csv_writer = csv.writer(temp_file)
        for member in memberships:
            try:
                member_id = int(''.join(filter(str.isdigit, str(member['ID']))))
                name = f"{member['FirstName']} {member['LastName']}"
                birth_date = datetime.strptime(member['BirthDate'], '%Y-%m-%d').date()
                csv_writer.writerow([member_id, name, birth_date])
            except Exception as e:
                logger.error(f"Error processing member {member.get('ID', 'unknown')}: {str(e)}")
                continue

        temp_file.close()  # Ensure the file is closed before using it in BULK INSERT

        # Use the absolute path for BULK INSERT
        file_path = temp_file.name.replace("\\", "\\\\")
        cursor.execute(f"""
        BULK INSERT #TempMembers
        FROM '{file_path}'
        WITH (
            FIELDTERMINATOR = ',',
            ROWTERMINATOR = '\\n',
            FIRSTROW = 1,
            TABLOCK
        );
        """)
    finally:
        # Clean up the temporary file after use
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)


def process_members(cursor, memberships):
    """Process memberships using a temporary table and stored procedure."""
    try:
        # Create the temporary table
        create_temp_table(cursor)
        logger.info("Temporary table created")

        # Bulk insert data into the temporary table
        bulk_insert_from_memory(cursor, memberships)
        logger.info("Bulk insert completed")

        # Call the stored procedure and fetch results
        cursor.execute("""
        DECLARE @MembershipTable MyMembershipType;

        INSERT INTO @MembershipTable (ID, Name, BirthDate)
        SELECT ID, Name, BirthDate FROM #TempMembers;

        EXEC dbo.RAFCalculator @Memberships = @MembershipTable;

        DROP TABLE #TempMembers;
        """)

        results = []
        for row in cursor.fetchall():
            results.append({
                'ID': row[0],
                'Name': row[1],
                'BirthDate': row[2].isoformat() if row[2] else None,
                'Age': row[3],
                'RiskScore': row[4]
            })

        return results

    except Exception as e:
        logger.error(f"Error in process_members: {str(e)}")
        cursor.execute("IF OBJECT_ID('tempdb..#TempMembers') IS NOT NULL DROP TABLE #TempMembers;")
        raise

@app.route('/process_data', methods=['POST'])
def process_data():
    """API endpoint to process membership data."""
    try:
        # Validate input
        data = request.json
        if not data or 'memberships' not in data:
            return jsonify({'error': 'No memberships data provided'}), 400

        memberships = data['memberships']
        if not memberships:
            return jsonify({'error': 'Empty memberships list'}), 400

        logger.info(f"Processing {len(memberships)} members")
        invalid_members = []
        valid_members = []

        for member in memberships:
            try:
                # Validate and parse each member
                member_id = int(''.join(filter(str.isdigit, str(member['ID']))))
                name = f"{member['FirstName']} {member['LastName']}"
                datetime.strptime(member['BirthDate'], '%Y-%m-%d').date()
                valid_members.append(member)
            except Exception as e:
                logger.warning(f"Invalid member data: {member} - {str(e)}")
                invalid_members.append({'member': member, 'error': str(e)})

        if not valid_members:
            return jsonify({'error': 'All memberships are invalid', 'details': invalid_members}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Process the valid members
            results = process_members(cursor, valid_members)
            conn.commit()

            return jsonify({
                'message': 'Data processed successfully',
                'count': len(results),
                'results': results,
                'invalid_members': invalid_members
            })

        except Exception as e:
            logger.error(f"Database operation error: {str(e)}")
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return jsonify({
            'error': str(e),
            'error_type': type(e).__name__
        }), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
