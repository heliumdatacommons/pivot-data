#!/usr/bin/env bash

PLUGIN_NAME='heliumdatacommons/cephfs'

rm -rf rootfs
docker build -t rootfsimage . --no-cache
id=$(docker create rootfsimage true)
mkdir -p rootfs
docker export "$id" | tar -x -C rootfs 2> /dev/null
docker rm -vf "$id"
docker rmi rootfsimage

docker plugin rm -f ${PLUGIN_NAME}
docker plugin create ${PLUGIN_NAME} .
docker plugin push ${PLUGIN_NAME}
