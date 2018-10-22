FROM alpine:latest


RUN apk add --no-cache --update --virtual=temporary curl gcc make build-base \
    && apk add --no-cache bash \
    && curl http://www.iozone.org/src/current/iozone3_434.tar > /tmp/iozone.tar \
    && cd /tmp \
    && tar -xf /tmp/iozone.tar \
    && cd /tmp/iozone*/src/current \
    && make linux \
    && cp iozone /usr/bin/iozone \
    && apk del temporary \
    && rm -rf /var/cache/apk/* /tmp/iozone*

ADD entrypoint.sh /bin/entrypoint.sh
RUN chmod +x /bin/entrypoint.sh

ENTRYPOINT ["/bin/entrypoint.sh"]