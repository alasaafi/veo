# Dockerfile

# Start with an official Python image
FROM python:3.11-slim

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Command to run your app
# ... all other lines above
# ... all other lines above
CMD gunicorn --bind 0.0.0.0:$PORT --timeout 120 app:app