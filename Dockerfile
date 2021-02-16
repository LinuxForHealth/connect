FROM python:3.8-alpine

RUN addgroup -S lfh && adduser -S lfh -G lfh -h /home/lfh

USER lfh

WORKDIR /home/lfh

COPY --chown=lfh:lfh ./pyconnect ./pyconnect
COPY --chown=lfh:lfh ./setup.py setup.py
COPY --chown=lfh:lfh ./README.md README.md
COPY --chown=lfh:lfh ./logging.yaml logging.yaml
RUN pip install --user -e .

CMD ["python", "/home/lfh/pyconnect/main.py"]