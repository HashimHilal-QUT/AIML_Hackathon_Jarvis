import pyodbc
import time
import json

destination_conn_str = (
    r'DRIVER={ODBC Driver 17 for SQL Server};'
    r'SERVER=20.84.125.50;'
    r'DATABASE=test;'
    r'UID=Healthtrixss;'
    r'PWD=P@ssword123;'
    r'CONNECTION TIMEOUT=60;'
)

def load_config(config_file):
    with open(config_file, 'r') as file:
        config = json.load(file)
    return config

def drop_table_if_exists(conn, table_name):
    cursor = conn.cursor()
    cursor.execute(f"""
    IF OBJECT_ID(N'{table_name}', N'U') IS NOT NULL
    BEGIN
        DROP TABLE {table_name}
    END
    """)
    conn.commit()

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
    rows = cursor.fetchall()
    tvp_data = []
    for row in rows:
        tvp_data.append(tuple(row))
    return tvp_data

def get_sql_type(pyodbc_type):
    type_map = {
        pyodbc.SQL_CHAR: 'NVARCHAR(MAX)',
        pyodbc.SQL_VARCHAR: 'NVARCHAR(MAX)',
        pyodbc.SQL_LONGVARCHAR: 'NVARCHAR(MAX)',
        pyodbc.SQL_WCHAR: 'NVARCHAR(MAX)',
        pyodbc.SQL_WVARCHAR: 'NVARCHAR(MAX)',
        pyodbc.SQL_WLONGVARCHAR: 'NVARCHAR(MAX)',
        pyodbc.SQL_DECIMAL: 'DECIMAL(18, 6)',
        pyodbc.SQL_NUMERIC: 'DECIMAL(18, 6)',
        pyodbc.SQL_SMALLINT: 'SMALLINT',
        pyodbc.SQL_INTEGER: 'INT',
        pyodbc.SQL_REAL: 'REAL',
        pyodbc.SQL_FLOAT: 'FLOAT',
        pyodbc.SQL_DOUBLE: 'FLOAT',
        pyodbc.SQL_BIT: 'BIT',
        pyodbc.SQL_TINYINT: 'TINYINT',
        pyodbc.SQL_BIGINT: 'BIGINT',
        pyodbc.SQL_BINARY: 'VARBINARY(MAX)',
        pyodbc.SQL_VARBINARY: 'VARBINARY(MAX)',
        pyodbc.SQL_LONGVARBINARY: 'VARBINARY(MAX)',
        pyodbc.SQL_TYPE_DATE: 'DATE',
        pyodbc.SQL_TYPE_TIME: 'TIME',
        pyodbc.SQL_TYPE_TIMESTAMP: 'DATETIME2',
    }
    return type_map.get(pyodbc_type, 'NVARCHAR(MAX)')

def create_table_if_not_exists(source_conn, dest_conn, source_table, target_table):
    source_cursor = source_conn.cursor()
    dest_cursor = dest_conn.cursor()
    
    # Get the schema of the source table
    source_cursor.execute(f"SELECT TOP 0 * FROM {source_table}")
    columns = [column[0] for column in source_cursor.description]
    column_types = [column[1] for column in source_cursor.description]
    
    # Create the table in the destination database
    create_query = f"IF OBJECT_ID(N'{target_table}', N'U') IS NULL BEGIN CREATE TABLE {target_table} ("
    for col, col_type in zip(columns, column_types):
        sql_type = get_sql_type(col_type)
        create_query += f"[{col}] {sql_type}, "
    create_query = create_query.rstrip(", ") + ") END"
    
    dest_cursor.execute(create_query)
    dest_conn.commit()

def execute_stored_procedure_with_tvp(tvp_data, destination_conn_str, procedure_name, target_table):
    try:
        dest_conn = pyodbc.connect(destination_conn_str)
        cursor = dest_conn.cursor()

        # Assuming the TVP type and procedure are already created
        cursor.execute(f"EXEC {procedure_name} @TVP = ?, @TargetTable = ?", (tvp_data, target_table))
        dest_conn.commit()

        # Fetching results
        cursor.execute(f"SELECT * FROM {target_table}")  # Use the target table name
        result_rows = cursor.fetchall()

        for row in result_rows:
            print(row)

        dest_conn.close()

    except Exception as e:
        print(f"An error occurred while executing stored procedure: {e}")

def dynamic_data_transfer_with_procedure(tables, source_conn_str, destination_conn_str, procedure_name):
    try:
        start_time = time.time()
        
        if not test_connection(source_conn_str, "source server"):
            raise Exception("Failed to connect to source server")
        
        if not test_connection(destination_conn_str, "destination server"):
            raise Exception("Failed to connect to destination server")
        
        source_conn = pyodbc.connect(source_conn_str)
        dest_conn = pyodbc.connect(destination_conn_str)
        
        for table in tables:
            source_table = table["source_table"]
            target_table = f"dbo.{table['target_table']}"  # Add 'dbo.' prefix

            print(f"Processing table: {source_table}")
            
            # Drop the target table if it exists in the destination database
            drop_table_if_exists(dest_conn, target_table)
            
            # Create the target table in the destination database
            create_table_if_not_exists(source_conn, dest_conn, source_table, target_table)
            
            # Extract data from source server
            cursor = source_conn.cursor()
            tvp_data = extract_data_as_tvp(cursor, source_table)
            
            # Pass the extracted data as a TVP to the destination stored procedure
            execute_stored_procedure_with_tvp(tvp_data, destination_conn_str, procedure_name, target_table)

        source_conn.close()
        dest_conn.close()

        end_time = time.time()
        duration = end_time - start_time

        print(f"Data transfer and procedure execution completed successfully.")
        print(f"Time taken: {duration:.2f} seconds")
        
    except Exception as e:
        print(f"An error occurred during data transfer: {e}")

if __name__ == '__main__':
    # User input for connection details
    source_server = input("Enter the source SQL Server address: ")
    source_database = input("Enter the source database name: ")
    source_user = input("Enter the source user ID: ")
    source_password = input("Enter the source password: ")
    source_tables = input("Enter the source table names (comma-separated for multiple tables): ").split(',')

    # Connection string for source
    source_conn_str = (
        r'DRIVER={ODBC Driver 17 for SQL Server};'
        f'SERVER={source_server};'
        f'DATABASE={source_database};'
        f'UID={source_user};'
        f'PWD={source_password};'
        r'CONNECTION TIMEOUT=60;'
    )

    # Prepare tables list in the format expected by the function
    tables = [{"source_table": table.strip(), "target_table": table.strip()} for table in source_tables]

    # Get procedure name 
    procedure_name = "dbo.usp_Process_MedScreeningTracker_FitKit"

    # Execute the data transfer and stored procedure
    dynamic_data_transfer_with_procedure(tables, source_conn_str, destination_conn_str, procedure_name)