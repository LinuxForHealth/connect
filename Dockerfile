FROM python:3.9.6-alpine3.14

ARG CONNECT_CERT_PATH_BUILD_ARG="./local-config/connect"
ARG CONNECT_CONFIG_PATH_BUILD_ARG="./local-config/connect"

RUN apk update && \
    apk add ca-certificates && \
    apk add --no-cache build-base \
        openssl \
        python3-dev \
        librdkafka-dev \
        librdkafka

# install certificates
# copy certificates and keys
WORKDIR /usr/local/share/ca-certificates/
COPY $CONNECT_CERT_PATH_BUILD_ARG/*.pem ./
COPY $CONNECT_CERT_PATH_BUILD_ARG/*.key ./
RUN chmod 644 *.pem *.key
RUN update-ca-certificates

# configure the connect app
RUN addgroup -S lfh && adduser -S lfh -G lfh -h /home/lfh

WORKDIR /home/lfh/connect
RUN mkdir config && \
    chown -R lfh:lfh /home/lfh/connect

# copy config files
COPY --chown=lfh:lfh $CONNECT_CERT_PATH_BUILD_ARG/nats-server.nk ./config/
COPY --chown=lfh:lfh Pipfile.lock logging.yaml ./

# configure application
COPY --chown=lfh:lfh ./connect ./connect
USER lfh
RUN python -m pip install --user --upgrade pip pipenv
RUN /home/lfh/.local/bin/pipenv sync

USER lfh
EXPOSE 5000
WORKDIR /home/lfh/connect
ENV PYTHONPATH="."
CMD ["/home/lfh/.local/bin/pipenv", "run", "python", "connect/main.py"]
