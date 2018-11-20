import os
import sys
import json
import logging

from tornado.httpclient import AsyncHTTPClient, HTTPError
from tornado.escape import json_encode, json_decode
from tornado.ioloop import IOLoop
from tornado.gen import sleep


def dirname(f):
  return os.path.dirname(os.path.abspath(f))


def message(status, content):
  return json_encode(dict(status_code=status, msg=content))


def error(status, content):
  return json_encode(dict(status_code=status, err=content))


async def run_async(func, *args):
  return await IOLoop.current().run_in_executor(None, func, *args)


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
      if cls not in cls._instances:
        cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
      return cls._instances[cls]


class Loggable(object):

  @property
  def logger(self):
    fmt = logging.Formatter('%(asctime)s|%(levelname)s|%(process)d|%(name)s.%(funcName)s'
                            '::%(lineno)s\t%(message)s')
    logger = logging.getLogger(self.__class__.__name__)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
      stream_hdlr = logging.StreamHandler(sys.stdout)
      stream_hdlr.setFormatter(fmt)
      file_hdlr = logging.FileHandler('%s/cephfs.log'%dirname(__file__))
      file_hdlr.setFormatter(fmt)
      logger.addHandler(stream_hdlr)
      logger.addHandler(file_hdlr)
    return logger


class AsyncHttpClientWrapper(Loggable):

  def __init__(self):
    self.__cli = AsyncHTTPClient()
    self.__headers = {'Content-Type': 'application/json'}

  async def get(self, host, port, endpoint, is_https=False, **headers):
    return await self._fetch(host, port, endpoint, 'GET', None, is_https, **headers)

  async def post(self, host, port, endpoint, body, is_https=False, **headers):
    return await self._fetch(host, port, endpoint, 'POST', body, is_https, **headers)

  async def put(self, host, port, endpoint, body=None, is_https=False, **headers):
    return await self._fetch(host, port, endpoint, 'PUT', body, is_https, **headers)

  async def delete(self, host, port, endpoint, body=None, is_https=False, **headers):
    return await self._fetch(host, port, endpoint, 'DELETE', body, is_https, **headers)

  async def _fetch(self, host, port, endpoint, method, body, is_https=False, **headers):
    protocol = 'https' if is_https else 'http'
    try:
      if isinstance(body, dict):
        body = json_encode(body)
      r = await self.__cli.fetch('%s://%s:%d%s'%(protocol, host, port, endpoint),
                                 method=method, body=body,
                                 headers=dict(**self.__headers, **headers),
                                 allow_nonstandard_methods=True)
      body = r.body.decode('utf-8')
      if body:
        body = json_decode(body)
      return 200, body, None
    except json.JSONDecodeError as de:
      return 422, None, error(422, de.msg)
    except HTTPError as e:
      if e.code == 599:
        return e.code, None, e.message
      return e.code, None, error(e.code, e.response.body.decode('utf-8'))
    except (ConnectionRefusedError, ConnectionResetError):
      self.logger.warning('Connection refused/reset, retry after 3 seconds')
      sleep(3)
      return await self._fetch(host, port, endpoint, method, body, is_https, **headers)