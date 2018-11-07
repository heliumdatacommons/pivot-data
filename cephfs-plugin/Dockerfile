FROM alpine:latest

RUN apk add --no-cache python3 py3-pip \
    && pip3 install --upgrade --no-cache-dir pip tornado==5.1.1 \
    && mkdir -p /mnt/cephfs \
    && mkdir -p /run/docker/plugins

COPY src /opt/src

EXPOSE 8888

ENTRYPOINT ["/usr/bin/python3", "/opt/src/plugin.py"]
