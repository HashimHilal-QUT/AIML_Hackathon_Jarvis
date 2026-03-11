import subprocess
import pyodbc
import time
import os
import json
import tempfile
import csv

# Connection strings with increased timeout
source_conn_str = (
    r'DRIVER={ODBC Driver 17 for SQL Server};'
    r'SERVER=10.0.0.4;'
    r'DATABASE=NYSalesDemo;'
    r'UID=karolbhandari;'
    r'PWD=karolbhandari@2024;'
    r'CONNECTION TIMEOUT=60;'
)

destination_conn_str = (
    r'DRIVER={ODBC Driver 17 for SQL Server};'
    r'SERVER=20.84.125.50;'
    r'DATABASE=test;'
    r'UID=Healthtrixss;'
    r'PWD=P@ssword123;'
    r'CONNECTION TIMEOUT=60;'
)

def load_config(config_file):
    try:
        with open(config_file, 'r') as file:
            content = file.read()
            print(f"Config file contents:\n{content}")
            config = json.loads(content)
        return config
    except FileNotFoundError:
        print(f"Config file not found: {config_file}")
        raise
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        print(f"Config file contents:\n{content}")
        raise
    except Exception as e:
        print(f"Unexpected error loading config: {e}")
        raise

def test_connection(conn_str, server_name):
    try:
        print(f"Attempting to connect to {server_name}...")
        conn = pyodbc.connect(conn_str, timeout=60)
        print(f"Successfully connected to {server_name}")
        conn.close()
        return True
    except pyodbc.Error as e:
        print(f"Failed to connect to {server_name}. Error: {str(e)}")
        return False

def get_table_schema(conn, table_name):
    cursor = conn.cursor()
    cursor.execute(f"SELECT TOP 0 * FROM {table_name}")
    return [column[0] for column in cursor.description]

def extract_data_as_tvp(cursor, table_name):
    cursor.execute(f"SELECT * FROM {table_name}")
    columns = [column[0] for column in cursor.description]
    rows = cursor.fetchall()
    return columns, rows

def execute_stored_procedure_with_tvp(columns, tvp_data, destination_conn_str, procedure_name, target_table):
    try:
        dest_conn = pyodbc.connect(destination_conn_str)
        cursor = dest_conn.cursor()

        # Create a temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', newline='', delete=False, suffix='.csv') as temp_file:
            csv_writer = csv.writer(temp_file, quoting=csv.QUOTE_ALL)
            csv_writer.writerow(columns)  # Write header
            csv_writer.writerows(tvp_data)
            temp_file_path = temp_file.name

        # Create a format file for bulk insert
        format_file_content = f"9.0\n{len(columns)}\n"
        for i, col in enumerate(columns, start=1):
            format_file_content += f"{i}       SQLCHAR       0       8000    \"\"      {i}     {col}               SQL_Latin1_General_CP1_CI_AS\n"

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.fmt') as format_file:
            format_file.write(format_file_content)
            format_file_path = format_file.name

        # Bulk insert data into the target table
        bulk_insert_query = f"""
        BULK INSERT {target_table}
        FROM '{temp_file_path.replace('\\', '\\\\')}'
        WITH (
            FORMATFILE = '{format_file_path.replace('\\', '\\\\')}',
            FIELDTERMINATOR = ',',
            ROWTERMINATOR = '\\n',
            FIRSTROW = 2,
            TABLOCK,
            KEEPNULLS
        )
        """
        cursor.execute(bulk_insert_query)
        dest_conn.commit()
        print(f"Inserted {len(tvp_data)} rows into {target_table}")

        # Execute the stored procedure
        exec_query = f"EXEC {procedure_name}"
        print(f"Executing query: {exec_query}")
        cursor.execute(exec_query)
        dest_conn.commit()

        # Fetching results (if any)
        try:
            cursor.execute("SELECT @ProcessedCount AS ProcessedCount")
            result = cursor.fetchone()
            if result:
                print(f"Total records processed: {result.ProcessedCount}")
        except pyodbc.ProgrammingError:
            print("No results returned from the stored procedure.")

        dest_conn.close()
        print(f"Stored procedure {procedure_name} executed successfully.")

    except Exception as e:
        print(f"An error occurred while executing stored procedure: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up temporary files
        if 'temp_file_path' in locals():
            os.remove(temp_file_path)
        if 'format_file_path' in locals():
            os.remove(format_file_path)

def dynamic_data_transfer_with_procedure(tables, source_conn_str, destination_conn_str, procedure_name):
    try:
        start_time = time.time()
        
        # Test connections separately
        if not test_connection(source_conn_str, "source server"):
            raise Exception("Failed to connect to source server")
        
        if not test_connection(destination_conn_str, "destination server"):
            raise Exception("Failed to connect to destination server")
        
        # Loop through all the tables configured by the client
        for table in tables:
            source_table = table["source_table"]
            target_table = table["target_table"]

            print(f"Processing table: {source_table}")
            
            # Extract data from source server
            source_conn = pyodbc.connect(source_conn_str)
            cursor = source_conn.cursor()
            columns, tvp_data = extract_data_as_tvp(cursor, source_table)
            print(f"Extracted {len(tvp_data)} rows from {source_table}")
            source_conn.close()
            
            # Pass the extracted data to the destination and execute the stored procedure
            print(f"Executing stored procedure: {procedure_name}")
            execute_stored_procedure_with_tvp(columns, tvp_data, destination_conn_str, procedure_name, target_table)

        end_time = time.time()
        duration = end_time - start_time

        print(f"Data transfer and procedure execution completed.")
        print(f"Time taken: {duration:.2f} seconds")
        
    except Exception as e:
        print(f"An error occurred during data transfer: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    config_file = 'config.json'  # JSON configuration file where the client can specify tables
    config = load_config(config_file)

    # List of tables to process and the stored procedure name
    tables = config["tables"]
    procedure_name = config["procedure_name"]

    dynamic_data_transfer_with_procedure(tables, source_conn_str, destination_conn_str, procedure_name)