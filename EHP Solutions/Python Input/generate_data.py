import json
import random
from datetime import datetime, timedelta

def generate_data(num_records=10000):
    first_names = ["John", "Jane", "Bob", "Alice", "Charlie", "Diana", "Edward", "Fiona", "George", "Hannah"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]

    current_date = datetime.now()
    start_date = current_date - timedelta(days=365*80)  # 80 years ago

    memberships = []
    for i in range(1, num_records + 1):
        birth_date = start_date + timedelta(days=random.randint(0, 365*80))
        year = random.randint(1, 30)  # Random year between 1 and 30
        
        record = {
            "ID": i,
            "FirstName": random.choice(first_names),
            "LastName": random.choice(last_names),
            "BirthDate": birth_date.strftime("%Y-%m-%d"),
            "Year": year
        }
        memberships.append(record)

    return {
        "memberships": memberships
    }

# Generate the data
data = generate_data(10000)

# Save to a JSON file
with open('generated_memberships.json', 'w') as f:
    json.dump(data, f, indent=2)

print("Data generated and saved to 'generated_memberships.json'")