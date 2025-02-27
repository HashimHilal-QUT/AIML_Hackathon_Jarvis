import pandas as pd
from uszipcode import SearchEngine
from datetime import datetime
import logging
import azure.functions as func
from azure.storage.blob import BlobServiceClient
import io
import os

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def clean_and_transform_manhattan_data(df):
    try:
        logging.info("Starting data transformation...")
        search = SearchEngine()
        type_conversions = {
            'RESIDENTIAL UNITS': 'float',
            'COMMERCIAL UNITS': 'float',
            'TOTAL UNITS': 'float',
            'LAND SQUARE FEET': 'float',
            'GROSS SQUARE FEET': 'float',
            'YEAR BUILT': 'float',
            'SALE PRICE': 'float'
        }
        for col, dtype in type_conversions.items():
            df[col] = pd.to_numeric(df[col], errors='coerce')

        df['ZIP CODE'] = df['ZIP CODE'].astype(str).str.extract('(\d{5})').fillna('00000')
        df = df[df['BOROUGH'] == '1']
        df['SALE DATE'] = pd.to_datetime(df['SALE DATE'], errors='coerce')

        def get_location_data(zip_code):
            try:
                result = search.by_zipcode(zip_code)
                return {
                    'major_city': str(result.major_city),
                    'county': str(result.county),
                    'state': str(result.state),
                    'lat': float(result.lat) if result.lat else 0,
                    'lng': float(result.lng) if result.lng else 0
                }
            except Exception as e:
                return None

        location_data = df['ZIP CODE'].apply(get_location_data)
        location_df = pd.DataFrame(location_data.tolist())
        df = pd.concat([df, location_df], axis=1)

        df['price_per_sqft'] = df['SALE PRICE'] / df['GROSS SQUARE FEET']
        df['residential_ratio'] = df['RESIDENTIAL UNITS'] / df['TOTAL UNITS']
        df['commercial_ratio'] = df['COMMERCIAL UNITS'] / df['TOTAL UNITS']

        df = df.replace([float('inf'), float('-inf')], None)

        return df

    except Exception as e:
        logging.error(f"Error in transformation: {str(e)}")
        raise

def get_blob_service_client():
    connection_string = os.environ["BLOB_CONNECTION_STRING"]
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    return blob_service_client

def read_blob(input_csv_path):
    blob_service_client = get_blob_service_client()
    container_name = os.environ["BLOB_CONTAINER_NAME"]
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=input_csv_path)
    download_stream = blob_client.download_blob()
    csv_data = download_stream.readall()
    df = pd.read_csv(io.BytesIO(csv_data))
    return df

def write_blob(df, output_csv_path):
    blob_service_client = get_blob_service_client()
    container_name = os.environ["BLOB_CONTAINER_NAME"]
    output_csv_buffer = io.StringIO()
    df.to_csv(output_csv_buffer, index=False)
    output_csv_buffer.seek(0)
    
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=output_csv_path)
    blob_client.upload_blob(output_csv_buffer.getvalue(), overwrite=True)

app = func.FunctionApp()

@app.route(route="transform_data")
def transform_data(req: func.HttpRequest) -> func.HttpResponse:
    setup_logging()
    input_csv_path = req.params.get('input_csv_path')
    output_csv_path = req.params.get('output_csv_path')

    if not input_csv_path or not output_csv_path:
        return func.HttpResponse(
            "Please provide both input_csv_path and output_csv_path as query parameters",
            status_code=400
        )

    try:
        logging.info(f"Reading input file from Blob Storage: {input_csv_path}")
        df = read_blob(input_csv_path)
        logging.info(f"Read {len(df)} records from CSV")
        
        transformed_df = clean_and_transform_manhattan_data(df)
        logging.info(f"Transformed data: {len(transformed_df)} records")
        
        logging.info(f"Writing output file to Blob Storage: {output_csv_path}")
        write_blob(transformed_df, output_csv_path)
        
        return func.HttpResponse(
            f"Data transformed successfully and saved to {output_csv_path}",
            status_code=200
        )
    
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)