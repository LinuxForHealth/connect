FROM alpine:3.13 AS builder

ARG APPLICATION_BUILD_CERT_PATH="./local-certs"
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

# copy certificates and keys
WORKDIR /usr/local/share/ca-certificates/
COPY $APPLICATION_BUILD_CERT_PATH/*.pem ./
COPY $APPLICATION_BUILD_CERT_PATH/*.key ./
RUN chmod 644 *.pem *.key

FROM python:3.9.4-alpine3.13

RUN apk update && \
    apk add --no-cache --virtual .dev-packages build-base curl bash

# build librdkafka
COPY --from=builder /usr/src/librdkafka /usr/src/librdkafka
RUN cd /usr/src/librdkafka && \
     ./configure --prefix=/usr --disable-lz4-ext && \
     make -j && \
     make install && \
     cd / && \
     rm -rf /usr/src/librdkafka

# install certificates
COPY --from=builder /usr/local/share/ca-certificates /usr/local/share/ca-certificates
RUN update-ca-certificates

# configure the connect app
RUN addgroup -S lfh && adduser -S lfh -G lfh -h /home/lfh

USER lfh

RUN mkdir -p /home/lfh/connect
WORKDIR /home/lfh/connect
COPY --chown=lfh:lfh ./connect ./connect
COPY --chown=lfh:lfh ./local-certs/nats-server.nk ./local-certs/
COPY --chown=lfh:lfh Pipfile.lock logging.yaml ./
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
