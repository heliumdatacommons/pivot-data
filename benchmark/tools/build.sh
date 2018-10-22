#!/usr/bin/env bash

OP=${1:-build-and-push}
TOOL=${2:-iozone}

if [ "${OP}" == 'build' -o "${OP}"='build-and-push' ];then
  docker build -t dchampion24/${TOOL} -f ${TOOL}/Dockerfile ${TOOL}
elif [ "${OP}" == 'push' -o "${OP}"='build-and-push' ];then
  docker push dchampion24/${TOOL}
fi
