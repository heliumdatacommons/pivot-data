#!/usr/bin/env bash

set -ex

MOUNTPOINT=${MOUNTPOINT:-/mnt}

mkdir -p ${MOUNTPOINT}

if [ -n "${FS_TYPE}" ];then
  if [ -n "${FS_OPTS}" ]; then
    for attempt in $(seq 3); do
      mount -t ${FS_TYPE} ${FS_HOST}:${FS_DIR} ${MOUNTPOINT} -o ${FS_OPTS}
      if [ "$?" = "0" ]; then
        echo "Mounted ${FS_HOST}:${FS_DIR} to ${MOUNTPOINT} successfully"
        break
      elif [ ${attempt} = "3" ];then
        echo "Failed to mount ${FS_HOST}:${FS_DIR} to ${MOUNTPOINT}"
        exit 1
      else
        echo "Attempt ${attempt}"
      fi
    done
  else
    for attempt in $(seq 3); do
      mount -t ${FS_TYPE} ${FS_HOST}:${FS_DIR} ${MOUNTPOINT}
      if [ "$?" = "0" ]; then
         echo "Mounted ${FS_HOST}:${FS_DIR} to ${MOUNTPOINT} successfully"
         break
      elif [ ${attempt} = "3" ];then
          echo "Failed to mount ${FS_HOST}:${FS_DIR} to ${MOUNTPOINT}"
          exit 1
      else
        echo "Attempt ${attempt}"
      fi
    done

  fi
fi

mkdir -p ${MOUNTPOINT}/${SUB_DIR}
cd ${MOUNTPOINT}/${SUB_DIR}

exec "${@}" | parse_output.py


function umount_fs() {
  umount -f ${MOUNTPOINT} \
  && echo "${MOUNTPOINT} is umounted successfully" \
  || echo "Failed to unmount ${MOUNTPOINT}"
}


if [ -n "${FS_TYPE}" ];then
  umount_fs
  umount_fs
fi
