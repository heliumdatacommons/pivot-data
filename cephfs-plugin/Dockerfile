FROM alpine:latest

RUN apk add --no-cache python3 py3-tornado \
    && mkdir -p /mnt/cephfs \
    && mkdir -p /run/docker/plugins

COPY src /opt/src

EXPOSE 8888

ENTRYPOINT ["/usr/bin/python3", "/opt/src/plugin.py"]
