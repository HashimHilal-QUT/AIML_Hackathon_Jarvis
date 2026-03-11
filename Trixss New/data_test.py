import subprocess
import pyodbc
import time
import os

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

def fast_data_transfer(source_table, target_table, source_conn_str, destination_conn_str):
    source_conn = None
    dest_conn = None
    try:
        start_time = time.time()
        
        # Test connections separately
        if not test_connection(source_conn_str, "source server"):
            raise Exception("Failed to connect to source server")
        
        if not test_connection(destination_conn_str, "destination server"):
            raise Exception("Failed to connect to destination server")
        
        # If both connections succeed, proceed with the data transfer
        source_conn = pyodbc.connect(source_conn_str)
        dest_conn = pyodbc.connect(destination_conn_str)
        
        # Get source table schema
        source_columns = get_table_schema(source_conn, source_table)
        
        # Create target table if it doesn't exist
        dest_cursor = dest_conn.cursor()
        create_table_query = f"IF OBJECT_ID('{target_table}', 'U') IS NULL CREATE TABLE {target_table} ({', '.join([f'[{col}] NVARCHAR(MAX)' for col in source_columns])})"
        dest_cursor.execute(create_table_query)
        dest_conn.commit()

        # Extract connection details
        source_details = dict(item.split('=') for item in source_conn_str.split(';') if item)
        dest_details = dict(item.split('=') for item in destination_conn_str.split(';') if item)

        # Temporary file for BCP
        temp_file = 'temp_data.dat'

        # Export data from source using BCP
        bcp_out_cmd = f"bcp {source_details['DATABASE']}.dbo.{source_table} out {temp_file} -S {source_details['SERVER']} -U {source_details['UID']} -P {source_details['PWD']} -c -t '|'"
        subprocess.run(bcp_out_cmd, shell=True, check=True)

        # Import data to destination using BCP
        bcp_in_cmd = f"bcp {dest_details['DATABASE']}.dbo.{target_table} in {temp_file} -S {dest_details['SERVER']} -U {dest_details['UID']} -P {dest_details['PWD']} -c -t '|'"
        subprocess.run(bcp_in_cmd, shell=True, check=True)

        # Clean up temporary file
        os.remove(temp_file)

        # Get row count
        dest_cursor.execute(f"SELECT COUNT(*) FROM {target_table}")
        total_rows = dest_cursor.fetchone()[0]

        end_time = time.time()
        duration = end_time - start_time
        
        print(f"Data transfer from {source_table} to {target_table} completed successfully.")
        print(f"Total rows transferred: {total_rows}")
        print(f"Time taken: {duration:.2f} seconds")
        print(f"Average speed: {total_rows / duration:.2f} rows/second")
        
    except Exception as e:
        print(f"An error occurred during data transfer: {e}")
    finally:
        if source_conn:
            source_conn.close()
        if dest_conn:
            dest_conn.close()

if __name__ == '__main__':
    source_table = 'stg_elig_staging_DataSource4_MedScreningTracker_FitKit'
    target_table = 'stg_elig_staging_DataSource4_MedScreningTracker_FitKit'  # You can change this if you want a different name in the target

    fast_data_transfer(source_table, target_table, source_conn_str, destination_conn_str)