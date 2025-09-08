FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# A simple command is enough for this new, lightweight app
CMD gunicorn --bind 0._0.0:$PORT --timeout 120 app:app