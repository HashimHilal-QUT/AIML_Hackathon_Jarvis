from flask import Flask, request, jsonify
import pyodbc
import subprocess
import time
import os
import json

app = Flask(__name__)


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

def load_config(config_file):
    try:
        with open(config_file, 'r') as file:
            config = json.load(file)
        return config
    except Exception as e:
        print(f"Error loading config: {e}")
        return None

def test_connection(conn_str, server_name):
    try:
        conn = pyodbc.connect(conn_str, timeout=60)
        conn.close()
        return True
    except pyodbc.Error as e:
        print(f"Failed to connect to {server_name}. Error: {str(e)}")
        return False

def execute_sqlcmd_and_procedure(source_conn_str, destination_conn_str, source_table, target_table, procedure_name, source_processed_table):
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
        raise

@app.route('/', methods=['GET'])
def home():
    return "Flask API is running. Use /call_procedure endpoint for data processing."

@app.route('/call_procedure', methods=['POST'])
def call_procedure():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        source_table = data.get('source_table')
        source_processed_table = data.get('source_processed_table')

        if not source_table or not source_processed_table:
            return jsonify({"error": "Missing required parameters"}), 400


        procedure_name = "ProcessMedScreeningData"
        if not procedure_name:
            return jsonify({"error": "Procedure name not found in configuration"}), 500

        if not test_connection(source_conn_str, "source server"):
            return jsonify({"error": "Failed to connect to source server"}), 500

        if not test_connection(destination_conn_str, "destination server"):
            return jsonify({"error": "Failed to connect to destination server"}), 500

        execute_sqlcmd_and_procedure(source_conn_str, destination_conn_str, source_table, source_table, procedure_name, source_processed_table)

        return jsonify({"message": "Procedure executed successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)