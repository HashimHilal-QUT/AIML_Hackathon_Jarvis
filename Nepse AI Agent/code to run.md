# Analyze a single stock (e.g., NABIL)
python run_analysis.py --mode single --symbol NABIL


# Analyze the entire market
python run_analysis.py --mode market

# Run market analysis every 30 minutes
python run_analysis.py --mode scheduled --interval 30


# Build the Docker image
docker build -t nepse-agent .

# Run single stock analysis
docker run nepse-agent python run_analysis.py --mode single --symbol NABIL

# Run market analysis
docker run nepse-agent python run_analysis.py --mode market

# Run scheduled analysis
docker run nepse-agent python run_analysis.py --mode scheduled --interval 30


# Analyze a single stock (e.g., NABIL)
python run_analysis.py --mode single --symbol NABIL