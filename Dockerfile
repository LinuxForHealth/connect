FROM alpine:3.13 AS builder

ARG LIBRDKAFKA_VERSION="v1.6.1"

RUN apk update
RUN apk add --no-cache curl

# install librdkafka from source as alpine package repositories may lag behind python confluent kafka requirements
# librdkafka installation procedure is attributed to https://github.com/confluentinc/confluent-kafka-python
RUN \
     echo Installing librdkafka && \
     mkdir -p /usr/src/librdkafka && \
     cd /usr/src/librdkafka && \
     curl -LfsS https://github.com/edenhill/librdkafka/archive/${LIBRDKAFKA_VERSION}.tar.gz | tar xvzf - --strip-components=1

FROM python:3.9.4-alpine3.13

ARG CONNECT_CERT_PATH_BUILD_ARG="./local-config/connect"
ARG CONNECT_CONFIG_PATH_BUILD_ARG="./local-config/connect"

RUN apk update && \
    apk add ca-certificates && \
    apk add --no-cache --virtual .dev-packages bash \
        build-base \
        curl \
        openssl

# build librdkafka
COPY --from=builder /usr/src/librdkafka /usr/src/librdkafka
RUN cd /usr/src/librdkafka && \
     ./configure --prefix=/usr --disable-lz4-ext && \
     make -j && \
     make install && \
     cd / && \
     rm -rf /usr/src/librdkafka

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

# hang onto dev packages until python libs are installed. Required for native dependencies.
USER root
RUN apk del .dev-packages

USER lfh
EXPOSE 5000
WORKDIR /home/lfh/connect
ENV PYTHONPATH="."
CMD ["/home/lfh/.local/bin/pipenv", "run", "python", "connect/main.py"]
