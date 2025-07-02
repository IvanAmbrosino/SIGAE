FROM debian:bookworm

RUN apt update && apt install -y \
    iputils-ping \
    curl \
    openssh-client \
    && apt clean

CMD [ "bash" ]