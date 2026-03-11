from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional, Union
from datetime import datetime, date
import aioodbc
import json
from contextlib import asynccontextmanager

# Pydantic models for request validation
class Membership(BaseModel):
    ID: Union[str, int] 
    FirstName: str
    LastName: str
    BirthDate: str

class MembershipRequest(BaseModel):
    memberships: List[Membership]

class MembershipResponse(BaseModel):
    message: str
    count: int
    results: List[dict]

app = FastAPI(
    title="RAF Calculator API",
    description="API for processing membership data and calculating RAF values",
    version="2.0.0"
)

# Connection settings
DB_CONFIG = {
    'driver': 'ODBC Driver 18 for SQL Server',
    'server': '10.10.1.4',
    'database': 'HTTEST',
    'user': 'karol_bhandari',
    'password': 'karolbhandari@2024'
}

# Connection pool manager
@asynccontextmanager
async def get_connection():
    dsn = (
        f'Driver={DB_CONFIG["driver"]};'
        f'Server={DB_CONFIG["server"]};'
        f'Database={DB_CONFIG["database"]};'
        f'UID={DB_CONFIG["user"]};'
        f'PWD={DB_CONFIG["password"]}'
    )
    conn = await aioodbc.connect(dsn=dsn, autocommit=True)
    try:
        yield conn
    finally:
        await conn.close()

async def get_table_type_info(cursor, type_name: str):
    query = """
    SELECT c.name, t.name as data_type, c.max_length, c.precision, c.scale
    FROM sys.table_types tt
    JOIN sys.columns c ON c.object_id = tt.type_table_object_id
    JOIN sys.types t ON t.user_type_id = c.user_type_id
    WHERE tt.name = ?
    ORDER BY c.column_id
    """
    await cursor.execute(query, (type_name,))
    result = await cursor.fetchall()
    return result

def to_string(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value) if value is not None else ''

@app.get("/", response_class=HTMLResponse)
async def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>RAF Calculator API</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                line-height: 1.6;
            }
            .endpoint {
                background-color: #f4f4f4;
                padding: 15px;
                border-radius: 5px;
                margin: 10px 0;
            }
            code {
                background-color: #e8e8e8;
                padding: 2px 5px;
                border-radius: 3px;
            }
        </style>
    </head>
    <body>
        <h1>RAF Calculator API Documentation</h1>
        <p>Welcome to the RAF Calculator API. This API provides endpoints for processing membership data.</p>
        
        <div class="endpoint">
            <h2>Process Data Endpoint</h2>
            <p><strong>URL:</strong> <code>/process_data</code></p>
            <p><strong>Method:</strong> POST</p>
            <p><strong>Description:</strong> Process membership data and calculate RAF values.</p>
            
            <h3>Request Format:</h3>
            <pre><code>
{
    "memberships": [
        {
            "ID": "string",
            "FirstName": "string",
            "LastName": "string",
            "BirthDate": "YYYY-MM-DD"
        }
    ]
}
            </code></pre>
            
            <h3>Response Format:</h3>
            <pre><code>
{
    "message": "Data processed successfully",
    "count": 0,
    "results": []
}
            </code></pre>
        </div>
        
        <div class="endpoint">
            <h2>API Documentation</h2>
            <p>For interactive API documentation, visit: <a href="/docs">/docs</a></p>
            <p>For alternative API documentation, visit: <a href="/redoc">/redoc</a></p>
        </div>
        
        <footer>
            <p>For more information, contact support.</p>
        </footer>
    </body>
    </html>
    '''

@app.post("/process_data", response_model=MembershipResponse)
async def process_data(request: MembershipRequest):
    try:
        async with get_connection() as conn:
            async with conn.cursor() as cursor:
                type_name = 'MyMembershipType'
                type_info = await get_table_type_info(cursor, type_name)
                columns = ', '.join([col[0] for col in type_info])
                
                all_results = []
                batch_size = 100
                for i in range(0, len(request.memberships), batch_size):
                    batch = request.memberships[i:i+batch_size]
                    values_list = []
                    
                    for member in batch:
                        try:
                            # Fixed ID handling
                            if isinstance(member.ID, int):
                                member_id = member.ID
                            else:
                                # Only try to extract digits if it's a string
                                numeric_id = ''.join(filter(str.isdigit, str(member.ID)))
                                member_id = int(numeric_id) if numeric_id else 0
                            
                            name = f"{member.FirstName} {member.LastName}"
                            birth_date = datetime.strptime(member.BirthDate, '%Y-%m-%d').date()
                            values_list.append((member_id, name, birth_date, 1))
                            
                        except Exception as e:
                            print(f"Error processing member {member.ID}: {str(e)}")
                            continue
                    
                    if not values_list:
                        continue
                    
                    # Create batch query
                    values_sql = ', '.join(['(?, ?, ?, ?)' for _ in range(len(values_list))])
                    sql = f"""
                    DECLARE @TempMemberships MyMembershipType;
                    DECLARE @Results NVARCHAR(MAX);

                    INSERT INTO @TempMemberships ({columns})
                    VALUES {values_sql};
                    
                    EXEC dbo.RAFCalculatorJson @Memberships=@TempMemberships, @Results=@Results OUTPUT;

                    SELECT @Results AS Results;
                    """
                    
                    try:
                        flat_values = [val for tup in values_list for val in tup]
                        await cursor.execute(sql, flat_values)
                        await cursor.nextset()
                        result = await cursor.fetchone()
                        
                        if result and result.Results:
                            parsed_results = json.loads(result.Results)
                            all_results.extend(parsed_results if isinstance(parsed_results, list) else [parsed_results])
                    
                    except Exception as e:
                        print(f"Error executing batch: {str(e)}")
                        continue

        return MembershipResponse(
            message='Data processed successfully',
            count=len(all_results),
            results=all_results
        )

    except Exception as e:
        import traceback
        print(f"Error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "error_type": type(e).__name__
            }
        )

@app.on_event("startup")
async def startup():
    # You can add startup tasks here, like initializing connection pools
    pass

@app.on_event("shutdown")
async def shutdown():
    # You can add cleanup tasks here
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5000,
        workers=4,  # Adjust based on your CPU cores
        http="httptools",  # Faster HTTP protocol implementation
    )