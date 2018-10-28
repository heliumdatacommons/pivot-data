#!/usr/bin/env bash

set -ex

MOUNTPOINT=${MOUNTPOINT:-/mnt}

mkdir -p ${MOUNTPOINT}

if [ -n "${FS_TYPE}" ];then
  if [ -n "${FS_OPTS}" ]; then
    mount -t ${FS_TYPE} ${FS_HOST}:${FS_DIR} ${MOUNTPOINT} -o ${FS_OPTS}
  else
    mount -t ${FS_TYPE} ${FS_HOST}:${FS_DIR} ${MOUNTPOINT}
  fi
  if [ "$?" = "0" ];then
    echo "Mounted ${FS_HOST}:${FS_DIR} to ${MOUNTPOINT} successfully"
  else
    echo "Failed to mount ${FS_HOST}:${FS_DIR} to ${MOUNTPOINT}"
    exit 1
  fi
fi

mkdir -p ${MOUNTPOINT}/${SUB_DIR}
cd ${MOUNTPOINT}/${SUB_DIR}

exec "${@}" | parse_output.py

if [ -n "${FS_TYPE}" ];then
  umount -f ${MOUNTPOINT} \
      && echo "${MOUNTPOINT} is umounted successfully" \
      || echo "Failed to unmount ${MOUNTPOINT}"
fi
