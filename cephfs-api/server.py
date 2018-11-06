import tornado
import asyncio

from tornado.web import RequestHandler

from tornado.httpserver import HTTPServer
from tornado.escape import json_encode, json_decode
from tornado.options import define, options

from ceph import Ceph
from container import DockerClient
from util import message, error

define('address', default='127.0.0.1', help='binding address')
define('port', default=8080, help='Port to listen on')
define('ceph_api_host', default='localhost', help='The host where Ceph REST API runs on')
define('ceph_api_port', default=5000, help='Port which Ceph REST API listens on')
define('ceph_daemon_image', default='ceph/daemon', help='Ceph daemon docker image')
define('ceph_config_dir', default='/opt/ceph/etc', help='Ceph configuration directory')
define('ceph_lib_dir', default='/opt/ceph/var/lib', help='Ceph library directory')


class FileSystemsHandler(RequestHandler):
  """

  """

  def initialize(self):
    self.__docker = DockerClient()
    self.__ceph = Ceph(options.ceph_api_host, options.ceph_api_port)

  async def get(self):
    _, fs_list, _ = await self.__ceph.list_fs()
    self.write(json_encode(fs_list))

  async def post(self):
    """
    {
      "name": "<fs-name>"
    }
    :return:
    """
    docker = self.__docker
    ceph_daemon_image = options.ceph_daemon_image
    cfg_dir, lib_dir = options.ceph_config_dir, options.ceph_lib_dir
    req = json_decode(self.request.body)
    name = req.get('name')
    if not name:
      self.set_status(400)
      self.write(error(400, '`name` is required'))
      return
    status, c, err = await docker.create_container(ceph_daemon_image, 'mds', 'cephfs-%s'%name,
                                                   environment=dict(CEPHFS_CREATE=1,
                                                                    CEPHFS_NAME=name,
                                                                    MDS_NAME='mds-%s'%name),
                                                   volumes={
                                                     cfg_dir: dict(bind='/etc/ceph', mode='rw'),
                                                     lib_dir: dict(bind='/var/lib/ceph', mode='rw')
                                                   })
    self.set_status(status)
    if status == 409:
      err = error(status, 'Filesystem `%s` already exists'%name)
    get_fs_status, _, _ = await self.__ceph.get_fs(name)
    while get_fs_status != 200:
      get_fs_status, _, _ = await self.__ceph.get_fs(name)
      await asyncio.sleep(1)
    self.write(message(status, 'Filesystem `%s` is created'%name) if c else err)


class FileSystemHandler(RequestHandler):

  def initialize(self):
    self.__docker = DockerClient()
    self.__ceph = Ceph(options.ceph_api_host, options.ceph_api_port)

  async def get(self, name):
    status, msg, err = await self.__ceph.get_fs(name)
    self.set_status(status)
    self.write(msg if status == 200 else err)

  async def delete(self, name):
    status, msg, err = await self.__docker.delete_container('cephfs-%s'%name)
    if status == 404:
      err = error(status, 'Filesystem `%s` is not found'%name)
    if status != 200:
      self.set_status(status)
      self.write(err)
      return
    status, msg, err = await self.__ceph.clean_fs(name)
    self.set_status(status)
    self.write(message(status, 'Filesystem `%s` has been deleted'%name) if status == 200 else err)


if '__main__' == __name__:
  tornado.options.parse_command_line()
  app = tornado.web.Application([
    (r'/fs', FileSystemsHandler),
    (r'/fs/([a-zA-Z0-9-]+)\/*', FileSystemHandler),
  ])
  server = HTTPServer(app)
  server.listen(options.port, address=options.address)
  tornado.ioloop.IOLoop.instance().start()
