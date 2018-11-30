import tornado

from json import JSONDecodeError
from tornado.web import RequestHandler
from tornado.httpserver import HTTPServer
from tornado.netutil import bind_unix_socket
from tornado.escape import json_encode, json_decode

from ceph import Ceph
from util import Loggable


class ActivateHandler(RequestHandler):
  """
  Indicate this plugin implements the VolumeDriver subsystem

  """

  async def post(self):
    self.write(json_encode(dict(Implements=['VolumeDriver'])))


class VolumeCapabilitiesHandler(RequestHandler, Loggable):
  """

  """

  async def post(self):
    self.write(json_encode(dict(Capabilities=dict(Scope='local'))))


class VolumeCreateHandler(RequestHandler, Loggable):
  """
  Invoked when a volume is being created.

  The plugin creates a new CephFS with the volume name specified in the request. The CephFS is
  created by calling the CephFS API running on the same host

  """

  def initialize(self):
    self.__ceph = Ceph()

  async def post(self):
    try:
      req = json_decode(self.request.body)
      status, msg, err = await self.__ceph.create_volume(req.get('Name'), req.get('Opts', {}))
      resp = json_encode(dict(Err=('' if status == 200 else err)))
    except JSONDecodeError as e:
      self.logger.error(e)
      status, resp = 422, json_encode(dict(Err='Unable to parse the request body'))
    self.set_status(status)
    self.write(resp)


class VolumeMountHandler(RequestHandler, Loggable):
  """
  Mount the CephFS to the `/propagatedMountPath/volumeName` using the Ceph kernel driver. The volume
  name is specified as the `mds_namespace` of the mount

  """

  def initialize(self):
    self.__ceph = Ceph()

  async def post(self):
    try:
      req = json_decode(self.request.body)
      status, mountpoint, err = await self.__ceph.mount_volume(req.get('Name'))
      resp = json_encode(dict(Mountpoint=mountpoint, Err='') if status == 200 else dict(Err=err))
    except JSONDecodeError as e:
      self.logger.error(e)
      status, resp = 422, json_encode(dict(Err='Unable to parse the request body'))
    self.set_status(status)
    self.write(resp)


class VolumePathHandler(RequestHandler, Loggable):
  """
  Return `/propagatedMountPath/volumeName`

  """

  def initialize(self):
    self.__ceph = Ceph()

  async def post(self):
    try:
      req = json_decode(self.request.body)
      status, mountpoint, err = await self.__ceph.get_volume(req.get('Name'))
      resp = json_encode(dict(Mountpoint=mountpoint, Err='') if status == 200 else dict(Err=err))
    except JSONDecodeError as e:
      self.logger.error(e)
      status, resp = 422, json_encode(dict(Err='Unable to parse the request body'))
    self.set_status(status)
    self.write(resp)


class VolumeUnmountHandler(RequestHandler, Loggable):
  """
  Unmount the CephFS using `umount -f`. The unmount step needs to be repeated for several times to
  force the unmount cleanly.

  Note that the unmount does not remove the CephFS instance but just unlinks it from the container

  """

  def initialize(self):
    self.__ceph = Ceph()

  async def post(self):
    try:
      req = json_decode(self.request.body)
      status, mountpoint, err = await self.__ceph.unmount_volume(req.get('Name'))
      resp = json_encode(dict(Err=('' if status == 200 else err)))
    except JSONDecodeError as e:
      self.logger.error(e)
      status, resp = 422, json_encode(dict(Err='Unable to parse the request body'))
    self.set_status(status)
    self.write(resp)


class VolumeGetHandler(RequestHandler, Loggable):
  """
  Get status of a volume

  """

  def initialize(self):
    self.__ceph = Ceph()

  async def post(self):
    try:
      req = json_decode(self.request.body)
      name = req.get('Name')
      status, mountpoint, err = await self.__ceph.get_volume(name)
      resp = json_encode(dict(Volume=dict(Name=name, Mountpoint=mountpoint), Err='')
                         if status == 200 else dict(Volume=dict(Name=name), Err=err))
    except JSONDecodeError as e:
      self.logger.error(e)
      status, resp = 422, json_encode(dict(Volume=dict(Name=name),
                                           Err='Unable to parse the request body'))
    self.set_status(status)
    self.write(resp)


class VolumeRemoveHandler(RequestHandler, Loggable):
  """
  Delete the CephFS instance including:

  - Delete the associated Ceph MDS
  - Delete the CephFS instance
  - Purge the associated data and metadata pools

  """

  def initialize(self):
    self.__ceph = Ceph()

  async def post(self):
    try:
      req = json_decode(self.request.body)
      status, mountpoint, err = await self.__ceph.delete_volume(req.get('Name'))
      resp = json_encode(dict(Err=('' if status == 200 else err)))
    except JSONDecodeError as e:
      self.logger.error(e)
      status, err = 422, json_encode(dict(Err='Unable to parse the request body'))
    self.set_status(status)
    self.write(resp)


class VolumeListHandler(RequestHandler, Loggable):
  """
  List all the volumes registered with the plugin. Since Ceph is distributed and CephFS instances
  are typically created in a distributed manner, this endpoint calls the CephFS API to get all the
  existing CephFS instances in the system.

  """
  def initialize(self):
    self.__ceph = Ceph()

  async def post(self):
    _, vols, _ = await self.__ceph.list_volumes()
    self.write(json_encode(dict(Volumes=list(vols), Err='')))


if '__main__' == __name__:
  app = tornado.web.Application([
    (r'/Plugin.Activate', ActivateHandler),
    (r'/VolumeDriver.Capabilities', VolumeCapabilitiesHandler),
    (r'/VolumeDriver.Create', VolumeCreateHandler),
    (r'/VolumeDriver.Remove', VolumeRemoveHandler),
    (r'/VolumeDriver.Mount', VolumeMountHandler),
    (r'/VolumeDriver.Unmount', VolumeUnmountHandler),
    (r'/VolumeDriver.Path', VolumePathHandler),
    (r'/VolumeDriver.Get', VolumeGetHandler),
    (r'/VolumeDriver.List', VolumeListHandler),
  ])
  server = HTTPServer(app)
  socket = bind_unix_socket('/run/docker/plugins/cephfs.sock')
  server.listen(8888)
  server.add_socket(socket)
  tornado.ioloop.IOLoop.instance().start()
