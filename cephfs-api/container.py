import shlex

from util import Singleton, Loggable, AsyncHttpClientWrapper


class MarathonClient(Loggable, metaclass=Singleton):

  def __init__(self, masters=[], port=8080):
    self.__masters = list(masters)
    self.__port = port
    self.__cli = AsyncHttpClientWrapper()

  async def create_container(self, name, group, image, command, privileged=False, network='host',
                             cpus=1, mem=2048, env={}, volumes={}):
    req = dict(id='/%s/%s'%(group, name),
               cpus=cpus, mem=mem, disk=0,
               args=shlex.split(command),
               env={str(k): str(v) for k, v in env.items()},
               container=dict(type='DOCKER',
                              volumes=list(volumes),
                              docker=dict(image=image,
                                          network=network.upper(),
                                          privileged=privileged,
                                          forcePullImage=True)),
               upgradeStrategy=dict(minimumHealthCapacity=0, maximumOverCapacity=0))
    return await self.__cli.post(self.__masters[0], self.__port, '/v2/apps', req)

  async def delete_container(self, name, group):
    return await self.__cli.delete(self.__masters[0], self.__port, '/v2/apps/%s/%s'%(group, name))


