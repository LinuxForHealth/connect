FROM python:3.9-alpine

ENV LIBRDKAFKA_VERSION v1.6.1

RUN apk update && \
    apk add --no-cache --virtual .dev-packages build-base curl bash

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

COPY --chown=lfh:lfh ./pyconnect ./pyconnect
COPY --chown=lfh:lfh ./setup.py setup.py
COPY --chown=lfh:lfh ./README.md README.md
COPY --chown=lfh:lfh ./logging.yaml logging.yaml
RUN pip install --user -e .

USER root
RUN apk del .dev-packages

USER lfh

EXPOSE 5000

CMD ["python", "/home/lfh/pyconnect/main.py"]
