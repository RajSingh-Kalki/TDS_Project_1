# Use a base image with Python
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install dependencies directly
RUN pip install fastapi uvicorn python-dotenv requests

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run the application
CMD ["python", "main.py"]
