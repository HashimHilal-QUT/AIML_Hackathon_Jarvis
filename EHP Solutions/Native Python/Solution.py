import subprocess
import pyodbc
import time
import os
import json
import io
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

def execute_sqlcmd_and_procedure(source_conn_str, destination_conn_str, source_table, target_table, procedure_name,source_processed_table):
    try:
        # Parse connection strings
        source_params = dict(param.split('=') for param in source_conn_str.split(';') if param)
        dest_params = dict(param.split('=') for param in destination_conn_str.split(';') if param)

        # Temporary files for BCP
        temp_data_file = 'temp_data.dat'
        temp_format_file = 'temp_format.fmt'

        # Create format file
        format_cmd = f"bcp {source_params['DATABASE']}.dbo.{source_table} format nul -c -f {temp_format_file} -S {source_params['SERVER']} -U {source_params['UID']} -P {source_params['PWD']}"
        print("Creating format file:", format_cmd)
        subprocess.run(format_cmd, shell=True, check=True)

        # Export data from source using BCP
        bcp_out_cmd = f"bcp {source_params['DATABASE']}.dbo.{source_table} out {temp_data_file} -S {source_params['SERVER']} -U {source_params['UID']} -P {source_params['PWD']} -c -t '|'"
        print("Executing BCP export command:", bcp_out_cmd)
        subprocess.run(bcp_out_cmd, shell=True, check=True)

        # Import data to destination using BCP
        bcp_in_cmd = f"bcp {dest_params['DATABASE']}.dbo.{target_table} in {temp_data_file} -S {dest_params['SERVER']} -U {dest_params['UID']} -P {dest_params['PWD']} -c -t '|'"
        print("Executing BCP import command:", bcp_in_cmd)
        subprocess.run(bcp_in_cmd, shell=True, check=True)

        # Clean up temporary files
        os.remove(temp_data_file)
        os.remove(temp_format_file)
        # Execute stored procedure
        dest_conn = pyodbc.connect(destination_conn_str)
        cursor = dest_conn.cursor()

        print(f"Executing stored procedure: {procedure_name}")
        cursor.execute(f"EXEC {procedure_name}")
        dest_conn.commit()
        print(f"Stored procedure {procedure_name} executed successfully.")

        # Get row count for Processed_MedScreningTracker_FitKit
        cursor.execute("SELECT COUNT(*) FROM Processed_MedScreningTracker_FitKit")
        processed_rows = cursor.fetchone()[0]
        print(f"Total rows in Processed_MedScreningTracker_FitKit: {processed_rows}")

        # Export data from Processed_MedScreningTracker_FitKit to a temporary file
        temp_processed_file = 'temp_processed_data.dat'
        bcp_out_processed_cmd = f"bcp {dest_params['DATABASE']}.dbo.Processed_MedScreningTracker_FitKit out {temp_processed_file} -S {dest_params['SERVER']} -U {dest_params['UID']} -P {dest_params['PWD']} -c -t '|'"
        print("Exporting processed data:", bcp_out_processed_cmd)
        subprocess.run(bcp_out_processed_cmd, shell=True, check=True)

        dest_conn.close()

        # Import processed data back to source database
        source_conn = pyodbc.connect(source_conn_str)
        source_cursor = source_conn.cursor()

        # Create or truncate the processed table in the source database
        source_cursor.execute(f"""
        IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[{source_processed_table}]') AND type in (N'U'))
        BEGIN
            SELECT TOP 0 * INTO [dbo].[{source_processed_table}]
            FROM [dbo].[{source_table}]
            
            -- Add First_Name and Last_Name columns
            ALTER TABLE [dbo].[{source_processed_table}]
            ADD [First_Name] NVARCHAR(255), [Last_Name] NVARCHAR(255)
        END
        ELSE
        BEGIN
            TRUNCATE TABLE [dbo].[{source_processed_table}]
        END
        """)
        source_conn.commit()

        # Import data to source database
        bcp_in_processed_cmd = f"bcp {source_params['DATABASE']}.dbo.{source_processed_table} in {temp_processed_file} -S {source_params['SERVER']} -U {source_params['UID']} -P {source_params['PWD']} -c -t '|'"
        print("Importing processed data back to source:", bcp_in_processed_cmd)
        subprocess.run(bcp_in_processed_cmd, shell=True, check=True)

        # Clean up temporary file
        os.remove(temp_processed_file)

        # Get row count for the processed table in source database
        source_cursor.execute(f"SELECT COUNT(*) FROM {source_processed_table}")
        source_processed_rows = source_cursor.fetchone()[0]
        print(f"Total rows in {source_processed_table} (source database): {source_processed_rows}")

        source_conn.close()

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
def dynamic_data_transfer_with_procedure(tables, source_conn_str, destination_conn_str, procedure_name):
    try:
        start_time = time.time()
        
        # Test connections separately
        if not test_connection(source_conn_str, "source server"):
            raise Exception("Failed to connect to source server")
        
        if not test_connection(destination_conn_str, "destination server"):
            raise Exception("Failed to connect to destination server")
        
        for table in tables:
            source_table = table["source_table"]
            target_table = table["target_table"]
            source_processed_table = table["source_processed_table"]

            print(f"Processing table: {source_table}")
            execute_sqlcmd_and_procedure(source_conn_str, destination_conn_str, source_table, target_table, procedure_name, "Tester")

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