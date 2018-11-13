import sys
import tornado
import asyncio

from tornado.web import RequestHandler

from tornado.httpserver import HTTPServer
from tornado.escape import json_encode, json_decode
from tornado.options import define, options

from ceph import Ceph
from container import MarathonClient
from util import message, error

define('address', default='0.0.0.0', help='binding address')
define('port', default=8080, help='Port to listen on')
define('ceph_api_host', default='localhost', help='The host where Ceph REST API runs on')
define('ceph_api_port', default=5000, help='Port which Ceph REST API listens on')
define('ceph_daemon_image', default='ceph/daemon', help='Ceph daemon docker image')
define('ceph_config_dir', default='/opt/ceph/etc', help='Ceph configuration directory')
define('ceph_lib_dir', default='/opt/ceph/var/lib', help='Ceph library directory')
define('marathon_masters', multiple=True, help='Marathon masters')
define('marathon_port', default=8080, help='Marathon port')


def validate_marathon_masters():
  if not options.marathon_masters or len(options.marathon_masters) == 0:
    sys.stderr.write('`marathon_masters` is required. '
                     'At least one Marathon master must be specified\n')
    sys.exit(1)


class FileSystemsHandler(RequestHandler):
  """

  """

  def initialize(self):
    self.__marathon = MarathonClient(options.marathon_masters, options.marathon_port)
    self.__ceph = Ceph(options.ceph_api_host, options.ceph_api_port)

  async def get(self):
    _, fs_list, _ = await self.__ceph.list_fs()
    self.write(json_encode(fs_list))

  async def post(self):
    """
    {
      "name": "<fs-name>",
      "appliance": "<appliance-name>"
    }
    :return:
    """
    marathon = self.__marathon
    ceph_daemon_image = options.ceph_daemon_image
    cfg_dir, lib_dir = options.ceph_config_dir, options.ceph_lib_dir
    req = json_decode(self.request.body)
    name, app = req.get('name'), req.get('appliance')
    if not name or not app:
      self.set_status(400)
      if not name:
        err_msg = '`name` is required'
      elif not app:
        err_msg = '`appliance` is required'
      self.write(error(400, err_msg))
    fs_name = '%s-%s'%(app, name)

    def volume(container_path, host_path, mode):
      return dict(containerPath=container_path, hostPath=host_path, mode=mode)

    status, c, err = await marathon.create_container('%s-%s'%(app, name), 'cephfs', ceph_daemon_image,
                                                     'mds',env=dict(CEPHFS_CREATE=1,
                                                                    CEPHFS_NAME=fs_name,
                                                                    MDS_NAME='mds-%s'%fs_name),
                                                     volumes=[
                                                       volume('/etc/ceph', cfg_dir, 'RW'),
                                                       volume('/var/lib/ceph', lib_dir, 'RW')
                                                     ])
    self.set_status(status)
    if status == 200:
      get_fs_status, _, _ = await self.__ceph.get_fs(fs_name)
      while get_fs_status != 200:
        get_fs_status, _, _ = await self.__ceph.get_fs(fs_name)
        await asyncio.sleep(1)
    elif status == 409:
      err = error(status, 'Filesystem `%s` for `%s` already exists' % (name, app))
    self.write(message(status, 'Filesystem `%s` for `%s` is created'%(name, app)) if c else err)


class FileSystemHandler(RequestHandler):

  def initialize(self):
    self.__marathon = MarathonClient(options.marathon_masters, options.marathon_port)
    self.__ceph = Ceph(options.ceph_api_host, options.ceph_api_port)

  async def get(self, app, name):
    status, msg, err = await self.__ceph.get_fs('%s-%s'%(app, name))
    self.set_status(status)
    self.write(msg if status == 200 else err)

  async def delete(self, app, name):
    status, msg, err = await self.__marathon.delete_container('%s-%s'%(app, name), 'cephfs')
    if status == 404:
      err = error(status, 'Filesystem `%s` for appliance `%s` is not found'%(name, app))
    if status != 200:
      self.set_status(status)
      self.write(err)
      return
    status, msg, err = await self.__ceph.clean_fs('%s-%s'%(app, name))
    self.set_status(status)
    self.write(message(status, 'Filesystem `%s` for appliance `%s` has been deleted'%(app, name))
               if status == 200 else err)


if '__main__' == __name__:
  tornado.options.parse_command_line()
  validate_marathon_masters()
  app = tornado.web.Application([
    (r'/fs', FileSystemsHandler),
    (r'/appliance/([a-zA-Z0-9-]+)/fs/([a-zA-Z0-9-]+)\/*', FileSystemHandler),
  ])
  server = HTTPServer(app)
  server.listen(options.port, address=options.address)
  tornado.ioloop.IOLoop.instance().start()
