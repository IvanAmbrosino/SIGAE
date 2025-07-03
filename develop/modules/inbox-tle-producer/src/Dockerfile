FROM python:3.13-slim

WORKDIR /app
COPY . /app/

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    bash \
    librdkafka-dev \
    python3-dev \
    libssl-dev \
 && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "__init__.py"]
