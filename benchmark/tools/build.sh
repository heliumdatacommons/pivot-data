#!/usr/bin/env bash

OP=${1:-build-and-push}
TOOL=${2:-iozone}
SUFFIX=${3:-latest}

if [ "${OP}" = 'build' ] || [ "${OP}" = 'build-and-push' ];then
  docker build -t dchampion24/${TOOL}:${SUFFIX} -f ${TOOL}/Dockerfile.${SUFFIX} ${TOOL}
fi 

if [ "${OP}" = 'push' ] || [ "${OP}" = 'build-and-push' ];then
  docker push dchampion24/${TOOL}:${SUFFIX}
fi
