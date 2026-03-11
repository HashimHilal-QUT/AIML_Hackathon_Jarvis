from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Union
import mysql.connector
from datetime import datetime, date
import logging
import uvicorn
import csv
import tempfile
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="RAF Calculator API")

# Database configuration
DB_CONFIG = {
    'host': '10.10.1.4',
    'database': 'HTTEST',
    'user': 'karol_bhandari',
    'password': 'karolbhandari@2024',
    # 'charset': 'utf8mb4',
    # 'allow_local_infile': True
}

class Member(BaseModel):
    ID: Union[str, int]  # Accept both string and integer
    FirstName: str
    LastName: str
    BirthDate: date

    @validator('BirthDate', pre=True)
    def parse_birthdate(cls, v):
        if isinstance(v, str):
            return datetime.strptime(v, '%Y-%m-%d').date()
        return v

    @validator('ID')
    def validate_id(cls, v):
        if isinstance(v, int):
            return str(v)
        return ''.join(filter(str.isdigit, str(v)))

class MemberRequest(BaseModel):
    memberships: List[Member]

class ProcessedMember(BaseModel):
    ID: int
    Name: str
    BirthDate: Optional[date]
    Age: Optional[int]
    RiskScore: Optional[float]

class APIResponse(BaseModel):
    message: str
    count: int
    results: List[ProcessedMember]
    invalid_members: List[dict] = []

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def create_temp_table(cursor):
    cursor.execute("""
    DROP TEMPORARY TABLE IF EXISTS TempMembers;
    CREATE TEMPORARY TABLE TempMembers (
        ID INT,
        Name VARCHAR(100),
        BirthDate DATE,
        INDEX IX_Temp_ID (ID)
    ) ENGINE=InnoDB;
    """)

async def batch_insert(cursor, memberships: List[Member]):
    temp_file_path = None
    try:
        # Create a temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, newline='') as temp_file:
            csv_writer = csv.writer(temp_file)
            for member in memberships:
                csv_writer.writerow([
                    int(member.ID),
                    f"{member.FirstName} {member.LastName}",
                    member.BirthDate.strftime('%Y-%m-%d')
                ])
            temp_file_path = temp_file.name

        # Load data from CSV file into temp table
        load_data_query = f"""
        LOAD DATA LOCAL INFILE '{temp_file_path}'
        INTO TABLE TempMembers
        FIELDS TERMINATED BY ','
        LINES TERMINATED BY '\\n'
        (ID, Name, BirthDate);
        """
        
        cursor.execute("SET GLOBAL local_infile = 1")
        cursor.execute(load_data_query)
        
        logger.info(f"Loaded {len(memberships)} records using LOAD DATA INFILE")

    except Exception as e:
        logger.error(f"Batch insert error: {str(e)}")
        raise
    finally:
        # Clean up the temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

async def process_members(cursor, memberships: List[Member]):
    try:
        create_temp_table(cursor)
        await batch_insert(cursor, memberships)

        # Adjust the stored procedure call for MySQL syntax
        cursor.execute("""
        CALL RAFCalculator(@result);
        SELECT * FROM TempMembers tm
        LEFT JOIN @result r ON tm.ID = r.ID;
        """)

        results = []
        for row in cursor.fetchall():
            logger.debug(f"Processing row: {row}")
            results.append(ProcessedMember(
                ID=row[0],
                Name=row[1],
                BirthDate=row[2],
                Age=int(row[4]) if row[4] is not None else None,
                RiskScore=float(row[5]) if row[5] is not None else None
            ))

        return results

    except Exception as e:
        logger.error(f"Error in process_members: {str(e)}")
        raise
    finally:
        cursor.execute("DROP TEMPORARY TABLE IF EXISTS TempMembers")

@app.get("/")
async def root():
    return {
        "message": "RAF Calculator API",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }

@app.post("/process_data", response_model=APIResponse)
async def process_data(request: MemberRequest):
    try:
        if not request.memberships:
            raise HTTPException(status_code=400, detail="Empty memberships list")

        logger.info(f"Processing {len(request.memberships)} members")

        conn = get_db_connection()
        cursor = conn.cursor(buffered=True)

        try:
            results = await process_members(cursor, request.memberships)
            conn.commit()

            return APIResponse(
                message="Data processed successfully",
                count=len(results),
                results=results,
                invalid_members=[]
            )

        except Exception as e:
            logger.error(f"Database operation error: {str(e)}")
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("api_v4:app", host="0.0.0.0", port=5002, workers=4)