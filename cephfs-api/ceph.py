from tornado.httputil import url_concat
from tornado.gen import multi

from util import AsyncHttpClientWrapper, Singleton, Loggable, message, error


class Ceph(Loggable, metaclass=Singleton):

  ENDPOINT_BASE = '/api/v0.1'

  def __init__(self, host='localhost', port=5000):
    super(Ceph, self).__init__()
    self.__cli = AsyncHttpClientWrapper()
    self.__host = host
    self.__port = port

  async def get_crush_map(self):
    status, output, err = await self._get('/osd/tree')
    if status != 200:
      return status, None, error(status, err)
    crush_map = {}
    nodes, node_map = output.get('nodes', []), {}
    for n in nodes:
      if n['type'] == 'root':
        continue
      node_map[n['id']] = n['type'], n['name']
    for n in nodes:
      if n['type'] == 'root':
        continue
      for c in n.get('children', []):
        if c not in node_map:
          continue
        crush_map[node_map[c]] = n['type'], n['name']
    return status, crush_map, None

  async def list_all_data_pools(self):
    status, pools, err = await self._get('/osd/pool/ls')
    return status, status == 200 and pools, status != 200 and error(status, err)

  async def create_data_pool(self, name, rule, n_replica=1, pg_num=8):
    if not rule:
      rule = 'replicated_rule'
    status, output, err = await self._put('/osd/pool/create', dict(pool=name,
                                                                   pg_num=pg_num, rule=rule))
    if status != 200:
      return status, None, error(status, err)
    if n_replica != 3:
      status, output, err = await self._put('/osd/pool/set', dict(pool=name,
                                                                  var='size', val=n_replica))
      if status != 200:
        self.logger.info(err)
    return status, message(200, 'Data pool `%s` has been created successfully'%name), None

  async def get_crush_rules(self):
    status, output, err = await self._get('/osd/crush/rule/ls')
    return status, status == 200 and output, status != 200 and error(status, err)

  async def get_crush_rule(self, name):
    status, output, err = await self._get('/osd/pool/get', dict(pool=name, var='crush_rule'))
    if status != 200:
      return status, None, error(status, err)
    return status, output['crush_rule'], None

  async def get_fs(self, name):
    status, output, err = await self._get('/fs/get', dict(fs_name=name))
    if status != 200:
      self.logger.debug(err)
      return 404, None, error(404, 'Filesystem `%s` is not found'%name)
    state = output.get('mdsmap', {}).get('info', {})
    if not state or len(state) == 0 or [v for v in state.values()][0].get('state') != 'up:active':
      return 503, None, error(503, 'Filesystem `%s` is not yet active'%name)

    async def get_placement(name):
      resps = await multi([self.get_crush_rule('%s_data' % name),
                           self.get_crush_map()])
      for i, (status, locality, err) in enumerate(resps):
        if status != 200:
          return status, None, err
        if i == 0:
          crush_rule = locality
        elif i == 1:
          crush_map = locality
      fs = crush_rule.split('_')[:-1]
      type, name = fs[0], '-'.join(fs[1:])
      locality = {type: name}
      while (type, name) in crush_map:
        type, name = crush_map[(type, name)]
        locality[type] = name
      return locality

    return status, dict(name=name, placement=await get_placement(name)), None

  async def list_fs(self):
    _, output, _ = await self._get('/fs/ls')
    return 200, [fs['name'] for fs in output], None

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
    resps = await multi([self.remove_data_pool(name), self.remove_metadata_pool(name)])
    for status, _, err in resps:
      if status != 200:
        self.logger.error(err.get('status', ''))
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
    status, out, err = await self.__cli.get(self.__host, self.__port, endpoint,
                                             accept='application/json', **headers)
    self.logger.debug('Output: %s'%out)
    self.logger.debug('Error: %s'%err)
    return status, status == 200 and out.get('output'), status != 200 and err.get('status', '')

  async def _put(self, endpoint, params={}, body=None, **headers):
    endpoint = self.ENDPOINT_BASE + endpoint
    if params:
      endpoint = url_concat(endpoint, params)
    status, out, err = await self.__cli.put(self.__host, self.__port, endpoint, body,
                                             accept='application/json', **headers)
    self.logger.debug('Output: %s'%out)
    self.logger.debug('Error: %s'%err)
    return status, status == 200 and out.get('output'), status != 200 and err.get('status', '')


