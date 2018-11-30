import os
import sys
import shlex
import shutil

from subprocess import Popen, PIPE
from multiprocessing import Lock
from tornado.escape import json_encode

from util import Loggable, AsyncHttpClientWrapper, Singleton, run_async


CEPHFS_API_HOST = str(os.environ.get('CEPHFS_API_HOST','127.0.0.1'))
CEPHFS_API_PORT = int(os.environ.get('CEPHFS_API_PORT', 8080))
PROPAGATED_MOUNT = '/mnt/cephfs'


class Ceph(Loggable, metaclass=Singleton):

  def __init__(self):
    self.__cli = AsyncHttpClientWrapper()
    self.__ceph_mon_host = self._get_ceph_mon_host()
    self.__lock = Lock()

  async def list_volumes(self):
    return await self._list_volumes()

  async def create_volume(self, name, opts={}):
    return await self.__cli.post(CEPHFS_API_HOST, CEPHFS_API_PORT, '/fs',
                                 body=json_encode(dict(name=name)))

  async def mount_volume(self, name):
    return await run_async(self._mount_volume, name)

  async def get_volume(self, name):
    return await self._get_volume(name)

  async def unmount_volume(self, name):
    return await run_async(self._unmount_volume, name)

  async def delete_volume(self, name):
    return await self._delete_volume(name)

  async def _list_volumes(self):

    def find_mountpoint(vols):
      vols = [dict(Name=v) for v in vols]
      for v in vols:
        mountpoint = '%s/%s' % (PROPAGATED_MOUNT, v['Name'])
        if os.path.exists(mountpoint) and os.path.ismount(mountpoint):
          v['Mountpoint'] = mountpoint
      return vols

    _, vols, _ = await self.__cli.get(CEPHFS_API_HOST, CEPHFS_API_PORT, '/fs')
    vols = await run_async(find_mountpoint, vols)
    return 200, vols, None

  def _mount_volume(self, name):
    mountpoint = '%s/%s'%(PROPAGATED_MOUNT, name)
    self.__lock.acquire()
    if not os.path.isdir(mountpoint):
      os.makedirs(mountpoint, mode=0o777)
    if os.path.ismount(mountpoint):
      self.__lock.release()
      return 200, mountpoint, None
    self.logger.info('mount -t ceph %s:/ %s ' 
                     '-o mds_namespace=%s'%(self.__ceph_mon_host, mountpoint, name))
    out, err = self._execute_cmd('mount -t ceph %s:/ %s ' 
                                 '-o mds_namespace=%s'%(self.__ceph_mon_host, mountpoint, name))
    if err:
      self.logger.error('Failed to mount: %s'%err)
      self.__lock.release()
      return 500, None, err
    self.__lock.release()
    return 200, mountpoint, None

  async def _get_volume(self, name):
    status, msg, err = await self.__cli.get(CEPHFS_API_HOST, CEPHFS_API_PORT, '/fs/%s'%name)
    if status == 404:
      self._unmount_volume(name)
      return status, None, err
    return 200, '%s/%s'%(PROPAGATED_MOUNT, name), None

  def _unmount_volume(self, name):
    mountpoint = '%s/%s'%(PROPAGATED_MOUNT, name)
    self.__lock.acquire()
    if os.path.exists(mountpoint) and os.path.ismount(mountpoint):
      self.logger.debug('Unmounting %s'%mountpoint)
      attempt = 0
      while attempt < 3:
        out, err = self._execute_cmd('umount -f %s'%mountpoint)
        if err:
          attempt += 1
          continue
        break
      if err:
        self.__lock.release()
        return 500, None, 'Failed to unmount %s: %s'%(mountpoint, err)
    self.__lock.release()
    return 200, None, None

  async def _delete_volume(self, name):
    mountpoint = '%s/%s' % (PROPAGATED_MOUNT, name)

    def remove_mountpoint(mountpoint):
      shutil.rmtree(mountpoint, ignore_errors=True)

    await run_async(remove_mountpoint, mountpoint)
    return await self.__cli.delete(CEPHFS_API_HOST, CEPHFS_API_PORT, '/fs/%s?purge=true' % name)

  def _execute_cmd(self, cmd):
    out, err = Popen(shlex.split(cmd), stdout=PIPE, stderr=PIPE).communicate()
    out, err = str(out, 'utf-8'), str(err, 'utf-8')
    return out, err

  def _get_ceph_mon_host(self):
    ceph_mon_host = os.environ.get('CEPH_MON_HOST')
    if not ceph_mon_host:
      sys.stderr.write('Missing required env `CEPH_MON_HOST`')
      sys.exit(1)
    return ceph_mon_host




