import pyodbc
import pandas as pd
import json
import os
from sqlalchemy import create_engine, Column, Integer, String, Date
from sqlalchemy.orm import declarative_base
from datetime import datetime
import urllib.parse
import time
from tqdm import tqdm

Base = declarative_base()

class Membership(Base):
    __tablename__ = 'memberships'
    
    ID = Column(Integer, primary_key=True)
    FirstName = Column(String(100))
    LastName = Column(String(100))
    BirthDate = Column(Date)
    Year = Column(Integer)

def custom_to_sql(df, name, con, chunksize=50000):
    total_rows = len(df)
    chunks = range(0, total_rows, chunksize)
    
    with tqdm(total=total_rows, desc="Loading data") as pbar:
        for start_i in chunks:
            end_i = min(start_i + chunksize, total_rows)
            if start_i == 0:
                df.iloc[start_i:end_i].to_sql(
                    name=name,
                    con=con,
                    if_exists='replace',
                    index=False
                )
            else:
                df.iloc[start_i:end_i].to_sql(
                    name=name,
                    con=con,
                    if_exists='append',
                    index=False
                )
            pbar.update(end_i - start_i)
            pbar.set_postfix(
                {'Chunk': f'{start_i+1:,}-{end_i:,}', 
                 'Remaining': f'{total_rows-end_i:,}'}
            )

def load_json_to_sql():
    total_start_time = time.time()
    print("Starting data load process...")
    try:
        # Read JSON file
        json_start_time = time.time()
        print("Reading JSON file...")
        with open('./generated_memberships.json', 'r') as file:
            json_data = json.load(file)
            if isinstance(json_data, dict):
                data = json_data.get(next(iter(json_data)), [])
            else:
                data = json_data
        json_end_time = time.time()
        print(f"JSON reading completed in {json_end_time - json_start_time:.2f} seconds")
        
        # Convert to DataFrame
        df_start_time = time.time()
        print("Converting to DataFrame...")
        df = pd.DataFrame(data)
        
        # Convert BirthDate to datetime
        print("Converting dates...")
        df['BirthDate'] = pd.to_datetime(df['BirthDate'])
        df['ID'] = df['ID'].astype(int)
        df['FirstName'] = df['FirstName'].astype(str)
        df['LastName'] = df['LastName'].astype(str)
        df['Year'] = df['Year'].astype(int)
        df_end_time = time.time()
        print(f"DataFrame conversion completed in {df_end_time - df_start_time:.2f} seconds")
        
        print("\nDataFrame preview:")
        print(df.head())
        print(f"Total records to be loaded: {len(df):,}")
        
        # Create SQLAlchemy engine connection to SQL Server
        db_start_time = time.time()
        print("\nCreating database connection...")
        params = urllib.parse.quote_plus(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            'SERVER=10.10.1.4;'
            'DATABASE=HTTEST;'
            'UID=karol_bhandari;'
            'PWD=karolbhandari@2024;'
            'TrustServerCertificate=yes;'
        )
        
        engine = create_engine(
            f'mssql+pyodbc:///?odbc_connect={params}',
            fast_executemany=False
        )
        
        # Create the table
        Base.metadata.create_all(engine)
        
        # Write to database using custom_to_sql method
        print("\nAttempting to write to database...")
        custom_to_sql(df, 'TempMemberships', engine)
        
        db_end_time = time.time()
        print(f"\nDatabase operations completed in {db_end_time - db_start_time:.2f} seconds")
        print(f"Average speed: {len(df)/(db_end_time - db_start_time):,.2f} records/second")
        print("Data successfully loaded to TempMemberships table!")
        
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        print("Error details:", type(e).__name__)
        import traceback
        print("Traceback:", traceback.format_exc())
        
    finally:
        if 'engine' in locals():
            engine.dispose()
            print("\nDatabase connection closed.")
        
        total_end_time = time.time()
        print(f"\nTotal execution time: {total_end_time - total_start_time:.2f} seconds")
        print(f"Total execution time: {(total_end_time - total_start_time) / 60:.2f} minutes")

if __name__ == "__main__":
    load_json_to_sql()
