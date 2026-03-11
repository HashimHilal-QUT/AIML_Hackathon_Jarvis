import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta

# Initialize Faker
fake = Faker()

# Set random seed for reproducibility
random.seed(42)
Faker.seed(42)
np.random.seed(42)

# Function to generate a unique ID
def generate_id(prefix, digits=8):
    return f"{prefix}{fake.unique.random_number(digits=digits, fix_len=True)}"

# Generate Membership data
def generate_membership_data(num_records=10000):
    data = []
    for _ in range(num_records):
        gender = random.choice(['M', 'F'])
        first_name = fake.first_name_male() if gender == 'M' else fake.first_name_female()
        last_name = fake.last_name()
        dob = fake.date_of_birth(minimum_age=18, maximum_age=90)
        member_id = generate_id('MEM')
        data.append({
            'MemberID': member_id,
            'FirstName': first_name,
            'LastName': last_name,
            'DateOfBirth': dob,
            'Gender': gender,
            'Email': fake.email(),
            'Phone': fake.phone_number(),
            'Address': fake.street_address(),
            'City': fake.city(),
            'State': fake.state_abbr(),
            'ZipCode': fake.zipcode(),
            'RegistrationDate': fake.date_between(start_date='-5y', end_date='today'),
            'MBI': f"1{fake.random_number(digits=10, fix_len=True)}",  # Simplified MBI for MBI Crosswalk
        })
    return pd.DataFrame(data)

# Generate Provider data
def generate_provider_data(num_providers=1000):
    data = []
    for _ in range(num_providers):
        provider_id = generate_id('PROV')
        data.append({
            'ProviderID': provider_id,
            'FirstName': fake.first_name(),
            'LastName': fake.last_name(),
            'Specialty': fake.job(),
            'Phone': fake.phone_number(),
            'Email': fake.email(),
            'Address': fake.street_address(),
            'City': fake.city(),
            'State': fake.state_abbr(),
            'ZipCode': fake.zipcode()
        })
    return pd.DataFrame(data)

# Generate sample data
membership_df = generate_membership_data(10000)
provider_df = generate_provider_data(1000)

# Generate MembershipEligibility data
eligibility_data = []
for _, member in membership_df.iterrows():
    coverage_start = fake.date_between(start_date='-2y', end_date='today')
    coverage_end = fake.date_between(start_date=coverage_start, end_date='+2y')
    eligibility_data.append({
        'MemberID': member['MemberID'],
        'CoverageStartDate': coverage_start,
        'CoverageEndDate': coverage_end,
        'PlanType': random.choice(['Gold', 'Silver', 'Bronze']),
        'CoverageType': random.choice(['Medical', 'Dental', 'Vision']),
        'RelationshipToSubscriber': random.choice(['Self', 'Spouse', 'Child', 'Other'])
    })

# Generate MemberPCP data
member_pcp_data = []
for _, member in membership_df.iterrows():
    pcp = provider_df.sample(n=1).iloc[0]
    assignment_date = fake.date_between(start_date='-2y', end_date='today')
    member_pcp_data.append({
        'MemberID': member['MemberID'],
        'ProviderID': pcp['ProviderID'],
        'AssignmentDate': assignment_date,
        'Status': random.choice(['Active', 'Inactive'])
    })

# Generate ClaimsHeader data
claims_header_data = []
for _ in range(20000):  # Generating more claims than members
    member = membership_df.sample(n=1).iloc[0]
    provider = provider_df.sample(n=1).iloc[0]
    service_date = fake.date_between(start_date='-1y', end_date='today')
    claims_header_data.append({
        'ClaimID': generate_id('CLM'),
        'MemberID': member['MemberID'],
        'ProviderID': provider['ProviderID'],
        'ServiceDate': service_date,
        'ClaimType': random.choice(['Medical', 'Dental', 'Vision']),
        'TotalCharges': round(random.uniform(100, 10000), 2),
        'ClaimStatus': random.choice(['Pending', 'Approved', 'Denied'])
    })

# Generate ClaimsDetail data
claims_detail_data = []
for claim in claims_header_data:
    for _ in range(random.randint(1, 5)):  # 1-5 line items per claim
        claims_detail_data.append({
            'ClaimID': claim['ClaimID'],
            'ServiceCode': fake.random_number(digits=5, fix_len=True),
            'ChargeAmount': round(random.uniform(10, 1000), 2),
            'PaymentAmount': round(random.uniform(0, 900), 2),
            'ServiceDescription': fake.sentence(nb_words=5)
        })

# Create DataFrames
eligibility_df = pd.DataFrame(eligibility_data)
member_pcp_df = pd.DataFrame(member_pcp_data)
claims_header_df = pd.DataFrame(claims_header_data)
claims_detail_df = pd.DataFrame(claims_detail_data)

# Combine all data into a single DataFrame
all_data = pd.concat([
    membership_df.assign(DatasetType='Membership'),
    eligibility_df.assign(DatasetType='MembershipEligibility'),
    provider_df.assign(DatasetType='Provider'),
    member_pcp_df.assign(DatasetType='MemberPCP'),
    claims_header_df.assign(DatasetType='ClaimsHeader'),
    claims_detail_df.assign(DatasetType='ClaimsDetail')
], ignore_index=True)

# Save to CSV
all_data.to_csv('healthcare_sample_data.csv', index=False)

print("Sample dataset created and saved as 'healthcare_sample_data.csv'")
print(f"Total rows: {len(all_data)}")
print(all_data['DatasetType'].value_counts())