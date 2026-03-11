import csv
import random
from datetime import datetime, timedelta
from tqdm import tqdm

def generate_data_to_csv(num_records=500000, filename='generated_memberships.csv'):
    first_names = ["John", "Jane", "Bob", "Alice", "Charlie", "Diana", "Edward", "Fiona", "George", "Hannah"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]

    current_date = datetime.now()
    start_date = current_date - timedelta(days=365*80)  # 80 years ago

    # Write to CSV with progress bar
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['ID', 'FirstName', 'LastName', 'BirthDate', 'Year']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # Write headers
        writer.writeheader()
        
        # Write data with progress bar
        for i in tqdm(range(1, num_records + 1), desc="Generating records"):
            birth_date = start_date + timedelta(days=random.randint(0, 365*80))
            year = random.randint(1, 30)
            
            record = {
                "ID": i,
                "FirstName": random.choice(first_names),
                "LastName": random.choice(last_names),
                "BirthDate": birth_date.strftime("%Y-%m-%d"),
                "Year": year
            }
            writer.writerow(record)

    print(f"Data generated and saved to '{filename}'")

if __name__ == "__main__":
    generate_data_to_csv(10000000)