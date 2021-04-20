FROM python:3.9.4-alpine3.13

ARG APPLICATION_BUILD_CERT_PATH="./local-certs"
ENV LIBRDKAFKA_VERSION="v1.6.1"
ENV APPLICATION_CERT_PATH="/usr/local/share/ca-certificates/"

RUN apk update && \
    apk add --no-cache --virtual .dev-packages build-base curl bash

# install certificates and keys
# certificates are in base64-encoded (PEM) format
COPY $APPLICATION_BUILD_CERT_PATH/*.pem $APPLICATION_CERT_PATH
RUN chmod 644 $APPLICATION_CERT_PATH/*.pem

COPY $APPLICATION_BUILD_CERT_PATH/*.key $APPLICATION_CERT_PATH
RUN chmod 644 $APPLICATION_CERT_PATH/*.key

RUN update-ca-certificates

# installing librdkafka from source as alpine package repositories may lag behind python confluent kafka requirements
# librdkafka installation procedure is attributed to https://github.com/confluentinc/confluent-kafka-python
RUN \
     echo Installing librdkafka && \
     mkdir -p /usr/src/librdkafka && \
     cd /usr/src/librdkafka && \
     curl -LfsS https://github.com/edenhill/librdkafka/archive/${LIBRDKAFKA_VERSION}.tar.gz | \
         tar xvzf - --strip-components=1 && \
     ./configure --prefix=/usr --disable-lz4-ext && \
     make -j && \
     make install && \
     cd / && \
     rm -rf /usr/src/librdkafka

RUN addgroup -S lfh && adduser -S lfh -G lfh -h /home/lfh

USER lfh
WORKDIR /home/lfh
COPY --chown=lfh:lfh ./connect ./connect
COPY --chown=lfh:lfh ./local-certs/nats-server.conf ./local-certs/server.nk ./local-certs/
COPY --chown=lfh:lfh setup.* README.md logging.yaml ./
RUN python -m pip install --upgrade pip setuptools
RUN python -m pip install --user -e .

USER root
RUN apk del .dev-packages

USER lfh
EXPOSE 5000
CMD ["python", "/home/lfh/connect/main.py"]
