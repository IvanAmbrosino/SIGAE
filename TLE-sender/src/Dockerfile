FROM python:3.10-alpine
WORKDIR /app
COPY . /app/
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    python3-dev \
    build-base \
    sshpass \
    bash \
    libssh2-dev
RUN pip install --upgrade pip
RUN apk add --no-cache librdkafka-dev python3-dev py3-pip gcc musl-dev
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "__init__.py"]
