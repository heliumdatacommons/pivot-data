import shlex

from tornado.gen import sleep
from util import Singleton, Loggable, AsyncHttpClientWrapper


class MarathonClient(Loggable, metaclass=Singleton):

  def __init__(self, masters=[], port=8080):
    self.__masters = list(masters)
    self.__port = port
    self.__cli = AsyncHttpClientWrapper()

  async def get_container(self, name, group):
    master, port = self.__masters[0], self.__port
    status, contr, err = await self.__cli.get(master, port, '/v2/apps/%s/%s'%(group, name))
    if status != 200:
      return status, contr, err
    tasks = contr.get('app', {}).get('tasks', [])
    if len(tasks) == 0 or tasks[0].get('state') != 'TASK_RUNNING':
      return 404, None, 'MDS of `%s` is not yet ready'%name
    return 200, 'MDS of `%s` is ready', None

  async def create_container(self, name, group, image, command, privileged=False, network='host',
                             cpus=.5, mem=1024, env={}, volumes={}, constraints=[]):
    req = dict(id='/%s/%s'%(group, name),
               cpus=cpus, mem=mem, disk=0,
               args=shlex.split(command),
               env={str(k): str(v) for k, v in env.items()},
               container=dict(type='DOCKER',
                              volumes=list(volumes),
                              docker=dict(image=image,
                                          network=network.upper(),
                                          parameters=[
                                            dict(key='rm', value='true')
                                          ],
                                          privileged=privileged,
                                          forcePullImage=True)),
               constraints=list(constraints),
               upgradeStrategy=dict(minimumHealthCapacity=0, maximumOverCapacity=0))
    return await self.__cli.post(self.__masters[0], self.__port, '/v2/apps', req)

  async def delete_container(self, name, group):
    master, port = self.__masters[0], self.__port
    status, msg, err = await self.__cli.delete(master, port, '/v2/apps/%s/%s'%(group, name))
    if status != 200:
      return status, msg, err
    _, deployments, _ = await self.__cli.get(master, port, '/v2/deployments')
    while any(['/%s/%s'%(group, name) in d.get('affectedApps', []) for d in deployments]):
      _, deployments, _ = await self.__cli.get(master, port, '/v2/deployments')
      await sleep(1)
    return status, msg, err


