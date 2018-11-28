import sys
import tornado

from json import JSONDecodeError
from tornado.gen import sleep, multi
from tornado.web import RequestHandler
from tornado.httpserver import HTTPServer
from tornado.escape import json_encode, json_decode
from tornado.options import define, options

from ceph import Ceph
from container import MarathonClient
from util import message, error, Loggable

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


class FileSystemsHandler(RequestHandler, Loggable):
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
      "data_n_replicas": <n-replica>,
      "metadata_n_replicas": <n-replica>,
      "placement": {
        "type": "<cloud/region/zone/host>",
        "value": "<val>"
      }
    }

    """
    marathon, ceph = self.__marathon, self.__ceph
    ceph_daemon_image = options.ceph_daemon_image
    cfg_dir, lib_dir = options.ceph_config_dir, options.ceph_lib_dir
    req = json_decode(self.request.body)
    name = req.get('name')
    if not name:
      self.set_status(400)
      self.write(error(400, '`name` is required'))
      return

    cephfs_status, _, _ = await ceph.get_fs(name)
    mds_status, _, _ = await marathon.get_container(name, 'cephfs')
    if cephfs_status == 200 and mds_status == 200:
      self.set_status(409)
      self.write(error(409, '`%s` already exists'%name))
      return

    data_n_replicas = req.get('data_n_replicas', 1)
    metadata_n_replicas = req.get('metadata_n_replicas', 1)

    async def validate_placement(p):
      if not isinstance(p, dict) \
          or 'type' not in p \
          or 'value' not in p:
        return None
      rule = '_'.join([p['type'], p['value'], 'rule']).replace('-', '_')
      _, rules, _ = await ceph.get_crush_rules()
      return rule if rule in rules else None

    placement, rule = req.get('placement'), None
    if placement:
      rule = await validate_placement(placement)
      if not rule:
        self.set_status(400)
        self.write(error(400, 'Invalid placement value'))
        return
    status, pools, err = await ceph.list_all_data_pools()
    if status != 200:
      self.set_status(status)
      self.write(err)
      return
    create_pool_funcs = []
    if '%s_data'%name not in pools:
      create_pool_funcs += [ceph.create_data_pool('%s_data'%name, rule, data_n_replicas)]
    if '%s_metadata'%name not in pools:
      create_pool_funcs += [ceph.create_data_pool('%s_metadata'%name, rule, metadata_n_replicas)]
    if len(create_pool_funcs) > 0:
      resps = await multi(create_pool_funcs)
      for status, _, err in resps:
        if status != 200:
          self.logger.error(err)
          self.set_status(500)
          self.write(error(500, 'Failed to create CephFS volume `%s`'%name))
          return

    def volume(container_path, host_path, mode):
      return dict(containerPath=container_path, hostPath=host_path, mode=mode)

    def placement_constraints():
      const = [['preemptible', 'CLUSTER', 'false']]
      if placement:
        const += [str(placement.type), 'CLUSTER', str(placement.value)]
      return const

    status, c, err = await marathon.create_container(name, 'cephfs', ceph_daemon_image, 'mds',
                                                     env=dict(CEPHFS_CREATE=1,
                                                              CEPHFS_NAME=name,
                                                              MDS_NAME='mds-%s'%name),
                                                     volumes=[
                                                       volume('/etc/ceph', cfg_dir, 'RW'),
                                                       volume('/var/lib/ceph', lib_dir, 'RW')
                                                     ],
                                                     constraints=placement_constraints())
    self.set_status(status)
    if status == 200:
      get_fs_status, _, _ = await self.__ceph.get_fs(name)
      while get_fs_status != 200:
        get_fs_status, _, _ = await self.__ceph.get_fs(name)
        await sleep(1)
    elif status == 409:
      err = error(status, 'Filesystem `%s` already exists'%name)
    self.write(message(status, 'Filesystem `%s` has been created'%name) if status == 200 else err)


class FileSystemHandler(RequestHandler, Loggable):

  def initialize(self):
    self.__marathon = MarathonClient(options.marathon_masters, options.marathon_port)
    self.__ceph = Ceph(options.ceph_api_host, options.ceph_api_port)

  async def get(self, name):
    status, msg, err = await self.__marathon.get_container(name, 'cephfs')
    if status != 200:
      self.set_status(status)
      self.write(err)
      return
    status, fs, err = await self.__ceph.get_fs(name)
    self.set_status(status)
    self.write(json_encode(fs) if status == 200 else err)

  async def delete(self, name):
    erasure = self.get_query_argument('erasure', False)
    if not isinstance(erasure, bool) and erasure.lower() not in ('true', 'false'):
      self.set_status(400)
      self.write(error(400, 'Unrecognized `erasure` value: %s'%erasure))
      return
    erasure = erasure and erasure.lower() == 'true'
    self.logger.debug('Erasure?: %s'%erasure)
    status, msg, err = await self.__marathon.delete_container(name, 'cephfs')
    if status == 404:
      self.logger.info('The MDS container for `%s` has already been deleted'%name)
    if status != 200 and status != 404:
      self.set_status(status)
      self.write(err)
      return
    msg = message(status, 'Filesystem `%s` has been deleted'%name)
    if erasure:
      status, msg, err = await self.__ceph.clean_fs(name)
      while status != 200:
        status, msg, err = await self.__ceph.clean_fs(name)
        await sleep(1)
      msg = message(status, 'Filesystem `%s` has been erased'%name)
    self.set_status(status)
    self.write(msg if status == 200 else err)


if '__main__' == __name__:
  tornado.options.parse_command_line()
  validate_marathon_masters()
  app = tornado.web.Application([
    (r'/fs\/*', FileSystemsHandler),
    (r'/fs/([a-zA-Z0-9-]+)\/*', FileSystemHandler),
  ])
  server = HTTPServer(app)
  server.listen(options.port, address=options.address)
  tornado.ioloop.IOLoop.instance().start()
