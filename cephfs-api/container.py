import docker

from docker.errors import APIError

from util import run_async, message, error, Singleton


class DockerClient(metaclass=Singleton):

  def __init__(self):
    self.__cli = docker.from_env()

  async def create_container(self, image, command, name,
                             privileged=False, network='host', environment={}, volumes={}):
    return await run_async(self._create_container, image, command, name,
                           privileged, network, environment, volumes)

  async def delete_container(self, name):
    return await run_async(self._delete_container, name)

  def _create_container(self, image, command, name,
                        privileged=False, network='host', environment={}, volumes={}):
    try:
      contr = self.__cli.containers.run(image, command,
                                        name='%s' % name,
                                        privileged=privileged,
                                        network=network,
                                        environment=dict(environment),
                                        volumes=dict(volumes),
                                        detach=True)
      return 201, contr, None
    except APIError as e:
      if e.status_code == 409:
        err = 'Container `%s` already exists'%name
      else:
        err = e.explanation
      return e.status_code, None, error(e.status_code, err)

  def _delete_container(self, name):
    try:
      contr = self.__cli.containers.get('%s'%name)
      contr.remove(force=True)
      return 200, message(200, 'Container `%s` has been removed'%name), None
    except APIError as e:
      if e.status_code == 404:
        err = 'Container `%s` is not found'%name
      else:
        err = e.explanation
      return e.status_code, None, error(e.status_code, err)


