import pyodbc
import pandas as pd

# Connection strings
source_conn_str = (
    r'DRIVER={ODBC Driver 17 for SQL Server};'
    r'SERVER=10.0.0.4;'
    r'DATABASE=HTTEST;'
    r'UID=karolbhandari;'
    r'PWD=karolbhandari@2024'
)

destination_conn_str = (
    r'DRIVER={ODBC Driver 17 for SQL Server};'
    r'SERVER=20.84.125.50;'
    r'DATABASE=test;'
    r'UID=Healthtrixss;'
    r'PWD=P@ssword123'
)

def get_db_connection(conn_str):
    return pyodbc.connect(conn_str)

def get_all_tables(conn_str):
    try:
        # Establish connection
        conn = get_db_connection(conn_str)
        cursor = conn.cursor()

        # Query to get all user tables in the database
        query = """
        SELECT TABLE_SCHEMA, TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
        """

        cursor.execute(query)
        tables = cursor.fetchall()

        # Store results in a list of dictionaries
        table_list = [{"schema": table[0], "name": table[1]} for table in tables]

        # Close the cursor and connection
        cursor.close()
        conn.close()

        return table_list

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def get_table_data(conn_str, schema, table_name):
    try:
        # Establish connection
        conn = get_db_connection(conn_str)

        # Query to select all data from the table
        query = f"SELECT * FROM [{schema}].[{table_name}]"

        # Read the data into a pandas DataFrame
        df = pd.read_sql(query, conn)

        # Close the connection
        conn.close()

        return df

    except Exception as e:
        print(f"An error occurred while fetching data from {schema}.{table_name}: {e}")
        return None

if __name__ == '__main__':
    # Get all tables from the source database
    tables = get_all_tables(source_conn_str)

    if tables:
        print("Tables in the database:")
        for table in tables:
            print(f"{table['schema']}.{table['name']}")
            
        # Example: Fetch data from the first table
        if tables:
            first_table = tables[0]
            print(f"\nFetching data from {first_table['schema']}.{first_table['name']}:")
            data = get_table_data(source_conn_str, first_table['schema'], first_table['name'])
            if data is not None:
                print(data.head())  # Print first few rows of the data
            else:
                print("Failed to fetch data from the table.")
    else:
        print("Failed to retrieve tables from the database.")