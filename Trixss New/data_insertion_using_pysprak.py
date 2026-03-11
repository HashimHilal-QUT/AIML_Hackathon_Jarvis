from flask import Flask, request, jsonify
import pyodbc
import os
from werkzeug.utils import secure_filename
import pandas as pd
from io import StringIO

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/path/to/upload'

conn_str = (
    r'DRIVER={ODBC Driver 17 for SQL Server};'
    r'SERVER=10.0.0.4;'
    r'DATABASE=HTTEST;'
    r'UID=karolbhandari;'
    r'PWD=karolbhandari@2024'
)

def get_db_connection():
    return pyodbc.connect(conn_str)

@app.route('/', methods=['GET'])
def home():
    return "Welcome to the API!"

@app.route('/call_procedure', methods=['POST'])
def call_procedure():
    try:
        # Establish connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # Create a temporary table to hold the TVP data
        cursor.execute("""
            IF OBJECT_ID('tempdb..#TempNewMemberships') IS NOT NULL
            DROP TABLE #TempNewMemberships;
                                
            CREATE TABLE #TempNewMemberships 
            (
                MembershipID INT,
                MemberName NVARCHAR(100),
                BirthDate DATE
            )
                        
            print 'Temp Table Created'

            insert into #TempNewMemberships
            select
                01, 'Samir Rawat','12/10/1999'

                                
            DECLARE @Memberships MyNewMembershipType

            INSERT INTO @Memberships (MembershipID, MemberName, BirthDate)
            SELECT * FROM #TempNewMemberships

            DECLARE @MembershipsOutbound MyNewMembershipTypeOutbound

            INSERT INTO @MembershipsOutbound 
            exec [dbo].[NewAgeCalculator] @Memberships

            drop table if exists #output
            select * into #output from @MembershipsOutbound
         """)
        cursor.execute("""select * from #output""")
        results = cursor.fetchall()  
        print("Results from TVP:", results)
        conn.commit() 
        
        result_list = [dict(zip([column[0] for column in cursor.description], row)) for row in results]

        # Close the cursor and connection
        cursor.close()
        conn.close()

        return jsonify(result_list), 200
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)