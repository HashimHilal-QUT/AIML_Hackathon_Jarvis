import pyodbc
import os
import pandas as pd
import re
import time
from datetime import datetime

EXPECTED_HEADER = ['EMPI', 'Member_ID', 'First_Name', 'Last_Name', 'PCP_Name', 'PCP_NPI', 'PCP_Fax', 'Sent_Date', 'Comments', 'Column_Header', 'Import_Date']

# Database connection parameters
username = 'karolbhandari'
password = 'karolbhandari@2024'
host = '10.0.0.4'
database_name = 'EasyHealthProd'
driver = 'ODBC Driver 17 for SQL Server'

# Step 1: Establish connection
def connect_to_db():
    connection_string = (
        f'DRIVER={{{driver}}};SERVER={host};DATABASE={database_name};'
        f'UID={username};PWD={password};Connection Timeout=30;'
    )
    return pyodbc.connect(connection_string)

# Test connection with a simple query
def test_connection(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    print(f"Connection test returned: {cursor.fetchone()[0]}")

def drop_all_tables(conn):
    cursor = conn.cursor()
    # Fetch all table names
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
    tables = cursor.fetchall()
    for table in tables:
        table_name = table[0]
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
    conn.commit()
    print("All tables dropped successfully.")

# Step 2: Convert folder name to target table name
def sanitize_foldername(foldername):
    sanitized_name = re.sub(r'[^a-zA-Z0-9]', '_', foldername)
    return f'stg_elig_{sanitized_name}'

def sanitize_column_name(column_name):
    # Initial sanitization
    sanitized_col = re.sub(r'[^a-zA-Z0-9]', '_', str(column_name).strip())
    
    # Replace double underscores with single underscore
    sanitized_col = re.sub(r'_{2,}', '_', sanitized_col)
    
    # Remove leading and trailing underscores
    sanitized_col = sanitized_col.strip('_')
    
    # Remove trailing underscore if it's not followed by any word
    sanitized_col = re.sub(r'_+$', '', sanitized_col)
    
    return sanitized_col

def ensure_unique_columns(columns):
    seen = set()
    unique_columns = []
    for col in columns:
        sanitized_col = sanitize_column_name(col)
        if sanitized_col in seen:
            counter = 1
            while f"{sanitized_col}_{counter}" in seen:
                counter += 1
            sanitized_col = f"{sanitized_col}_{counter}"
        unique_columns.append(sanitized_col)
        seen.add(sanitized_col)
    return unique_columns

def create_staging_table(conn, file_path, table_name):
    if file_path.endswith('.xlsx'):
        xlsx = pd.ExcelFile(file_path)
        print(f"Worksheets in {file_path}: {xlsx.sheet_names}")
        
        # Read the first sheet to set the headers
        main_df = pd.read_excel(xlsx, sheet_name=xlsx.sheet_names[0], header=0)
        
        # Clean column names
        main_df.columns = [str(col).strip() for col in main_df.columns]
        
        # Ensure unique column names
        main_df.columns = ensure_unique_columns(main_df.columns)
        
        # Add sheet_name column for the first sheet
        main_df['sheet_name'] = xlsx.sheet_names[0]
        
        # Print number of columns and rows in the first sheet
        print(f"Sheet '{xlsx.sheet_names[0]}' has {len(main_df.columns)} columns and {len(main_df)} rows.")
        
        # Process remaining sheets
        for sheet_name in xlsx.sheet_names[1:]:
            df = pd.read_excel(xlsx, sheet_name=sheet_name, header=None)
            
            # Print number of columns and rows in the current sheet
            print(f"Sheet '{sheet_name}' has {len(df.columns)} columns and {len(df) - 1} rows (excluding header).")
            
            # Use the first row as data
            df.columns = main_df.columns[:-1]  # Align columns with the first sheet, excluding 'sheet_name'
            df = df.iloc[1:].reset_index(drop=True)  # Skip the first row
            
            # Add sheet_name column for the current sheet
            df['sheet_name'] = sheet_name
            
            # Append to main_df, filling missing columns with NaN
            main_df = pd.concat([main_df, df], ignore_index=True, sort=False)
        
        # Add new columns
        main_df['filename'] = os.path.splitext(os.path.basename(file_path))[0]
        main_df['Imported_Date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    elif file_path.endswith('.csv'):
        main_df = pd.read_csv(file_path, header=0)  # Use the first row as header
        main_df.columns = [sanitize_column_name(col) for col in main_df.columns]
        main_df.columns = ensure_unique_columns(main_df.columns)
        print(f"Total rows in CSV file: {len(main_df)}")

    # Save a copy of the final DataFrame to CSV
    csv_file_path = f"{os.path.splitext(file_path)[0]}_combined.csv"
    main_df.to_csv(csv_file_path, index=False)
    print(f"Combined data saved to {csv_file_path}")

    # Create the table
    column_definitions = ', '.join([f'[{col}] VARCHAR(MAX)' for col in main_df.columns])
    cursor = conn.cursor()
    cursor.execute(f'DROP TABLE IF EXISTS {table_name}')
    cursor.execute(f'CREATE TABLE {table_name} ({column_definitions})')
    conn.commit()

    # Print total rows in merged dataframe
    total_rows = len(main_df)
    print(f"Total rows in merged dataframe {table_name}: {total_rows}")

    return table_name, main_df

def remove_additional_headers(df, header_values):
    replication_mask = df.apply(lambda row: row.tolist() == header_values, axis=1)
    return df[~replication_mask].reset_index(drop=True)

# Step 3: Load data
def load_data_to_table(conn, table_name, df):
    if df.empty:
        print(f"No data to load for table: {table_name}")
        return
    
    success = bcp_load_data(conn, table_name, df)
    
    if not success:
        print("BCP load failed. Falling back to row-by-row insertion.")
        cursor = conn.cursor()
        df = df.where(pd.notnull(df), None)
        column_names = ', '.join([f'[{col}]' for col in df.columns])
        placeholders = ', '.join('?' * len(df.columns))

        for row in df.itertuples(index=False, name=None):
            try:
                cursor.execute(
                    f'INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})',
                    [None if pd.isna(v) else v for v in row]
                )
            except Exception as e:
                print(f"Error inserting row: {row} into table: {table_name} - {e}")
        conn.commit()

def bcp_load_data(conn, table_name, df):
    temp_csv = f'temp_data_{os.getpid()}.csv'
    df.to_csv(temp_csv, index=False, header=False, sep='|', date_format='%Y-%m-%d %H:%M:%S', escapechar='\\')
    
    bcp_command = f"bcp {table_name} in {temp_csv} -c -t'|' -S {host} -U {username} -P {password} -d {database_name} -e error_{os.getpid()}.log"
    result = os.system(bcp_command)
    
    if result == 0:
        print(f"Successfully loaded {len(df)} rows into {table_name} using BCP")
    else:
        print(f"BCP command failed. Check error_{os.getpid()}.log for details.")
    
    try:
        os.remove(temp_csv)
    except FileNotFoundError:
        print(f"Warning: Could not delete temporary file {temp_csv}")
    
    return result == 0

def process_file(file_path, table_name):
    # Use the file name (without extension) to create the table name
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    table_name = sanitize_foldername(file_name)  # Reuse the sanitize function for consistency
    print(file_name,table_name)

    max_retries = 3
    retries = 0
    while retries < max_retries:
        try:
            conn = connect_to_db()
            table_name, df = create_staging_table(conn, file_path, table_name)
            if not df.empty:
                # Add new columns before loading data
                df['filename'] = os.path.splitext(os.path.basename(file_path))[0]
                df['Imported_Date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                load_data_to_table(conn, table_name, df)
            conn.close()
            print(f"Processed file: {file_path} into table: {table_name}")
            print(f"Total rows in {table_name}: {len(df)}")
            return len(df)
        except pyodbc.Error as e:
            retries += 1
            print(f"Error processing file: {file_path} ({e}) - Retry {retries}/{max_retries}")
            time.sleep(5)  # wait before retrying
        except Exception as e:
            print(f"Error processing file: {file_path}", e)
            break
    return 0

def combine_files(files):
    all_dfs = []
    all_columns = set()
    
    # First pass: read all files and collect all unique columns
    for file in files:
        if file.endswith('.csv'):
            df = pd.read_csv(file, low_memory=False, parse_dates=True, infer_datetime_format=True)
        elif file.endswith('.xlsx'):
            df = pd.read_excel(file, parse_dates=True)
        df['filename'] = os.path.basename(file)
        all_dfs.append(df)
        all_columns.update(df.columns)
    
    # Find the DataFrame with the most columns
    max_columns_df = max(all_dfs, key=lambda df: len(df.columns))
    
    # Create a new DataFrame with all columns from the file with maximum headers
    combined_df = pd.DataFrame(columns=list(max_columns_df.columns) + ['filename'])
    
    # Second pass: align and append data from all DataFrames
    for df in all_dfs:
        aligned_df = pd.DataFrame(columns=combined_df.columns)
        for col in df.columns:
            if col in aligned_df.columns:
                aligned_df[col] = df[col]
        combined_df = pd.concat([combined_df, aligned_df], ignore_index=True)
    if combined_df.index.duplicated().any():
        print("Duplicate index values found. Handling duplicates...")
    # Option 1: Remove duplicates
    combined_df = combined_df[~combined_df.index.duplicated(keep='first')]
    
    print(f"Total rows in combined DataFrame: {len(combined_df)}")
    print(f"Total columns in combined DataFrame: {len(combined_df.columns)}")
    
    return combined_df

def main():
    conn = connect_to_db()
    # Uncomment the following line if you ever need to drop all tables
    # drop_all_tables(conn)
    conn.close()

    base_directory = '/Users/karolbhandari/Desktop/EHP Solutions/Python Input'
    print("Base directory exists, listing files...")

    # List all files in the directory
    files = [os.path.join(base_directory, f) for f in os.listdir(base_directory) if f.endswith('.xlsx') or f.endswith('.csv')]

    if not files:
        print("No .xlsx or .csv files found in the directory.")
        return

    print(f"Found files: {files}")

    total_rows_processed = 0
    for file_path in files:
        table_name = sanitize_foldername(os.path.basename(os.path.dirname(file_path)))
        rows_processed = process_file(file_path, table_name)
        total_rows_processed += rows_processed

    print(f"\nTotal rows processed across all files: {total_rows_processed}")

    conn = connect_to_db()
    test_connection(conn)
    conn.close()

if __name__ == "__main__":
    main()