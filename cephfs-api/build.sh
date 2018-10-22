#!/usr/bin/env bash

docker build -t dchampion24/cephfs-api -f docker/Dockerfile .
docker push dchampion24/cephfs-api