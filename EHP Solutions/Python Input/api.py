import pyodbc
from datetime import datetime, date
import json

# Connection string for the destination database
destination_conn_str = (
    r'DRIVER={SQL Server};'
    r'SERVER=10.10.1.4;'  # Replace with your server's IP or hostname
    r'DATABASE=HTTEST;'
    r'UID=karol_bhandari;'  # Your SQL Server username
    r'PWD=karolbhandari@2024;'  # Your SQL Server password
)

# Path to your CSV file
csv_file_path = r'C:\path\to\generated_memberships.csv'  # Adjust file path as needed

try:
    # Establish connection to the SQL Server database
    conn = pyodbc.connect(destination_conn_str)
    cursor = conn.cursor()

    # SQL to perform BULK INSERT
    bulk_insert_query = f"""
    BULK INSERT TempMemberships
    FROM '{csv_file_path}'
    WITH (
        FIELDTERMINATOR = ',', 
        ROWTERMINATOR = '\\n', 
        FIRSTROW = 2
    );
    """

    # Execute the bulk insert query
    cursor.execute(bulk_insert_query)
    conn.commit()
    print("Data loaded successfully.")

except pyodbc.Error as e:
    print(f"Error: {e}")

finally:
    # Clean up
    if cursor:
        cursor.close()
    if conn:
        conn.close()
