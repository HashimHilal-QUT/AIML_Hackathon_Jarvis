# Use the official Python image as the base
FROM python:3.11
 
# Set the working directory inside the container
WORKDIR /app
 
# Install AutoGen Studio
RUN pip install autogenstudio
 
# Expose the port that AutoGen Studio uses
EXPOSE 8081
 
# Command to launch AutoGen Studio UI and bind to all interfaces
CMD ["autogenstudio", "ui", "--host", "0.0.0.0"]