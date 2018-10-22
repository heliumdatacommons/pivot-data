#!/usr/bin/env bash

set -e

MOUNTPOINT=${MOUNTPOINT:-/mnt}

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
  fi
fi

cd ${MOUNTPOINT}

exec ${@}

if [ -n "${FS_TYPE}" ];then
  umount -f ${MOUNTPOINT} \
      && echo "${MOUNTPOINT} is umounted successfully" \
      || echo "Failed to unmount ${MOUNTPOINT}"
fi
