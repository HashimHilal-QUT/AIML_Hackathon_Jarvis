import requests
import json
import time
from datetime import datetime

# Start timing
start_time = time.time()
print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Read JSON file
with open('generated_memberships.json', 'r') as file:
    data = json.load(file)
    print(f"Number of records to process: {len(data['memberships'])}")

# API endpoint
url = "http://10.10.1.5:5010/process_data"

# Headers
headers = {
    'Content-Type': 'application/json'
}

# Send POST request
print("\nSending request...")
response = requests.post(url, json=data, headers=headers)

# Calculate execution time
end_time = time.time()
execution_time = end_time - start_time

# Print response and timing information
print("\nResponse:")
print(response.json())
print(f"\nExecution Statistics:")
print(f"Total time: {execution_time:.2f} seconds")
print(f"Time per record: {(execution_time/len(data['memberships'])*1000):.2f} ms")
print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")