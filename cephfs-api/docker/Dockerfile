FROM alpine:latest

COPY requirements.txt /tmp/requirements.txt

RUN apk add --no-cache --update python3 py3-pip \
    && pip3 install --upgrade --no-cache-dir pip \
    && pip3 install --no-cache-dir -r /tmp/requirements.txt

COPY . /opt/cephfs-api
ENV DOCKER_HOST 'unix://var/run/docker.sock'

ENTRYPOINT ["/usr/bin/python3", "/opt/cephfs-api/server.py"]
