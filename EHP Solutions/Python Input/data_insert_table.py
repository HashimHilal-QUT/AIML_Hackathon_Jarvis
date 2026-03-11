import json
import random
from datetime import datetime, timedelta
import pyodbc
import tqdm

def generate_and_insert_data(num_records=500000):
    # Connection string
    destination_conn_str = (
    r'DRIVER={ODBC Driver 17 for SQL Server};'
        r'SERVER=10.10.1.4;'
        r'DATABASE=ClientEndAnalystDataDB;'
        r'UID=karol_bhandari;'
        r'PWD=karolbhandari@2024;'
    )

    # Sample data
    first_names = ["John", "Jane", "Bob", "Alice", "Charlie", "Diana", "Edward", "Fiona", "George", "Hannah"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]

    current_date = datetime.now()
    start_date = current_date - timedelta(days=365*80)  # 80 years ago

    # Connect to database
    try:
        conn = pyodbc.connect(destination_conn_str)
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'jay' AND schema_id = SCHEMA_ID('dbo'))
            CREATE TABLE dbo.jay (
                ID int PRIMARY KEY,
                FirstName varchar(50),
                LastName varchar(50),
                BirthDate date,
                Year int
            )
        """)
        
        # Batch insert for better performance
        batch_size = 1000
        for i in tqdm.tqdm(range(1, num_records + 1), desc="Inserting records"):
            birth_date = start_date + timedelta(days=random.randint(0, 365*80))
            year = random.randint(1, 30)
            
            cursor.execute("""
                INSERT INTO dbo.jay (ID, FirstName, LastName, BirthDate, Year)
                VALUES (?, ?, ?, ?, ?)
            """, (
                i,
                random.choice(first_names),
                random.choice(last_names),
                birth_date.strftime("%Y-%m-%d"),
                year
            ))
            
            if i % batch_size == 0:
                conn.commit()
        
        # Final commit for any remaining records
        conn.commit()
        print(f"Successfully inserted {num_records} records into the jay table")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    generate_and_insert_data(500000)