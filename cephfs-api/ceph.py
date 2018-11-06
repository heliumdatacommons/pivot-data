from tornado.httputil import url_concat

from util import AsyncHttpClientWrapper, Singleton, Loggable, message, error


class Ceph(Loggable, metaclass=Singleton):

  ENDPOINT_BASE = '/api/v0.1'

  def __init__(self, host='localhost', port=5000):
    super(Ceph, self).__init__()
    self.__cli = AsyncHttpClientWrapper()
    self.__host = host
    self.__port = port

  async def get_fs(self, name):
    status, output, _ = await self._get('/fs/get', dict(fs_name=name))
    if status != 200:
      return 404, None, error(404, 'Filesystem `%s` is not found'%name)
    state = output.get('output', {}).get('mdsmap', {}).get('info', {})
    if not state or len(state) == 0 or [v for v in state.values()][0].get('state') != 'up:active':
      return 503, None, error(503, 'Filesystem `%s` is not yet active'%name)
    return status, message(200, 'Filesystem `%s` is ready'%name), None

  async def list_fs(self):
    _, msg, _ = await self._get('/fs/ls')
    return 200, [fs['name'] for fs in msg.get('output', [])], None

  async def clean_fs(self, name):
    status, _, err = await self.fail_mds(name)
    errmsg = error(500, 'Failed to clean up filesystem `%s`'%name)
    if status != 200:
      self.logger.error(err)
      return status, _, errmsg
    status, _, err = await self.remove_fs(name)
    if status != 200:
      self.logger.error(err)
      return status, _, errmsg
    status, _, err = await self.remove_data_pool(name)
    if status != 200:
      self.logger.error(err)
      return status, _, errmsg
    status, _, err = await self.remove_metadata_pool(name)
    if status != 200:
      self.logger.error(err)
      return status, _, errmsg
    return status, message(status, 'Filesystem `%s` has been cleaned up'%name), _

  async def fail_mds(self, name):
    status, _, err = await self._put('/mds/fail',
                                     dict(who='mds-%s'%name))
    if status == 200:
      return status, message(status, 'MDS `%s` has been failed'%name), _
    return status, None, error(status, err)

  async def remove_fs(self, name):
    status, _, err = await self._put('/fs/rm',
                                     dict(fs_name=name, sure='--yes-i-really-mean-it'))
    if status == 200:
      return status, message(status, 'Filesystem `%s` has been removed'%name), _
    return status, None, error(status, err)

  async def remove_data_pool(self, name):
    status, _, err = await self._put('/osd/pool/rm',
                                     dict(pool='%s_data'%name, pool2='%s_data'%name,
                                          sure='--yes-i-really-really-mean-it'))
    if status == 200:
      return status, message(status, 'Data pool of filesystem `%s` has been removed'%name), _
    return status, _, error(status, err)

  async def remove_metadata_pool(self, name):
    status, _, err = await self._put('/osd/pool/rm',
                                     dict(pool='%s_metadata'%name, pool2='%s_metadata'%name,
                                          sure='--yes-i-really-really-mean-it'))
    if status == 200:
      return status, message(status, 'Metadata pool of filesystem `%s` has been removed'%name), _
    return status, _, error(status, err)

  async def _get(self, endpoint, params={}, **headers):
    endpoint = self.ENDPOINT_BASE + endpoint
    if params:
      endpoint = url_concat(endpoint, params)
    return await self.__cli.get(self.__host, self.__port, endpoint, accept='application/json',
                                **headers)

  async def _put(self, endpoint, params={}, body=None, **headers):
    endpoint = self.ENDPOINT_BASE + endpoint
    if params:
      endpoint = url_concat(endpoint, params)
    return await self.__cli.put(self.__host, self.__port, endpoint, body, accept='application/json',
                                **headers)


