import pyodbc
import time
from sqlalchemy import create_engine
import pandas as pd

# Connection strings
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

def fast_data_transfer(source_table, target_table, source_conn_str, destination_conn_str):
    try:
        start_time = time.time()
        
        # Test connections
        if not test_connection(source_conn_str, "source server"):
            raise Exception("Failed to connect to source server")
        if not test_connection(destination_conn_str, "destination server"):
            raise Exception("Failed to connect to destination server")
        
        # Create SQLAlchemy engines
        source_engine = create_engine(f"mssql+pyodbc:///?odbc_connect={source_conn_str}")
        dest_engine = create_engine(f"mssql+pyodbc:///?odbc_connect={destination_conn_str}")
        
        # Read data from source in chunks
        chunksize = 100000  # Adjust this based on your available memory
        chunks = pd.read_sql_table(source_table, source_engine, chunksize=chunksize)
        
        # Write data to destination
        total_rows = 0
        for chunk in chunks:
            chunk.to_sql(target_table, dest_engine, if_exists='append', index=False)
            total_rows += len(chunk)
            print(f"Transferred {total_rows} rows...")
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"Data transfer from {source_table} to {target_table} completed successfully.")
        print(f"Total rows transferred: {total_rows}")
        print(f"Time taken: {duration:.2f} seconds")
        print(f"Average speed: {total_rows / duration:.2f} rows/second")
        
    except Exception as e:
        print(f"An error occurred during data transfer: {e}")

if __name__ == '__main__':
    source_table = 'stg_elig_staging_DataSource2_ContactActivity'
    target_table = 'stg_elig_staging_DataSource2_ContactActivity'

    fast_data_transfer(source_table, target_table, source_conn_str, destination_conn_str)