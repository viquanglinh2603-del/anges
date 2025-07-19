FROM python:3.12.7-slim

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5005

# Use a shell form for CMD so that ${APP_PASSWORD} can be expanded at runtime
CMD ["sh", "-c", "python run_web_interface.py --host 0.0.0.0 --port 5005 --password ${APP_PASSWORD}"]
