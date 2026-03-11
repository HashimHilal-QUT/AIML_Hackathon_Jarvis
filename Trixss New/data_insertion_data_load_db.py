from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.sql.types import StructType, StructField, StringType, FloatType, DateType

# Create a Spark session
spark = SparkSession.builder \
    .appName("HealthcareDataLoader") \
    .config("spark.jars.packages", "mysql:mysql-connector-java:8.0.28") \
    .getOrCreate()

# Define the schema for our data
schema = StructType([
    StructField("DatasetType", StringType(), True),
    StructField("MemberID", StringType(), True),
    StructField("ProviderID", StringType(), True),
    StructField("ClaimID", StringType(), True),
    StructField("FirstName", StringType(), True),
    StructField("LastName", StringType(), True),
    StructField("DateOfBirth", DateType(), True),
    StructField("Gender", StringType(), True),
    StructField("Email", StringType(), True),
    StructField("Phone", StringType(), True),
    StructField("Address", StringType(), True),
    StructField("City", StringType(), True),
    StructField("State", StringType(), True),
    StructField("ZipCode", StringType(), True),
    StructField("RegistrationDate", DateType(), True),
    StructField("MBI", StringType(), True),
    StructField("CoverageStartDate", DateType(), True),
    StructField("CoverageEndDate", DateType(), True),
    StructField("PlanType", StringType(), True),
    StructField("CoverageType", StringType(), True),
    StructField("RelationshipToSubscriber", StringType(), True),
    StructField("Specialty", StringType(), True),
    StructField("AssignmentDate", DateType(), True),
    StructField("Status", StringType(), True),
    StructField("ServiceDate", DateType(), True),
    StructField("ClaimType", StringType(), True),
    StructField("TotalCharges", FloatType(), True),
    StructField("ClaimStatus", StringType(), True),
    StructField("ServiceCode", StringType(), True),
    StructField("ChargeAmount", FloatType(), True),
    StructField("PaymentAmount", FloatType(), True),
    StructField("ServiceDescription", StringType(), True)
])

# Read the CSV file
df = spark.read.csv("healthcare_sample_data.csv", header=True, schema=schema)

# Convert date columns
date_columns = ['DateOfBirth', 'RegistrationDate', 'CoverageStartDate', 'CoverageEndDate', 'AssignmentDate', 'ServiceDate']
for col_name in date_columns:
    df = df.withColumn(col_name, col(col_name).cast(DateType()))

# MySQL connection properties
mysql_properties = {
    "driver": "com.mysql.cj.jdbc.Driver",
    "url": "jdbc:mysql://localhost:3306/your_database_name",
    "user": "your_username",
    "password": "your_password"
}

# Write the data to MySQL
df.write \
    .mode("append") \
    .jdbc(url=mysql_properties["url"],
          table="healthcare_data",
          properties=mysql_properties)

print("Data insertion completed.")

# Stop the Spark session
spark.stop()