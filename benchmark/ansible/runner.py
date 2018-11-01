import os
import sys
import yaml
import shlex
import shutil
import numpy as np

from subprocess import Popen, PIPE, STDOUT

exp_id = 'ff95ca6b7c3c0b37ffca953f541eaa3d9e6d749a'
n_repeat = 10

clients = {
  # 'rbd': dict(host='10.52.100.16', type='nfs', dir='/', opts='vers=4'),
  # 'cephfs': dict(host='10.52.100.11', type='ceph', dir='/', opts='mds_namespace=alpha'),
  'nfsv4': dict(host='10.52.100.3', type='nfs', dir='/', opts='vers=4'),
  # 'ganesha': dict(host='10.52.100.23', type='nfs', dir='/', opts='vers=4'),
  # 'gfganesha': dict(host='10.52.100.3', type='nfs', dir='/data', opts='vers=4'),
  # 'rbdganesha': dict(host='10.52.100.9', type='nfs', dir='/', opts='vers=4'),
}


def update_client_config(host, type, dir, opts, zone=[], n_parallel=1):
  fn = 'group_vars/all.yml'
  cfg = yaml.load(open(fn))
  cfg['client'].update(host=host, type=type, dir=dir, opts=opts, n_parallel=n_parallel)
  cfg['zone'] = list(zone)
  yaml.dump(cfg, open(fn, 'w'),
            default_flow_style=False,
            allow_unicode=True,
            encoding=None)


def shuffle_clients():
  clis = list(clients.items())
  np.random.shuffle(clis)
  return clis


def run_experiment():
  p = Popen(shlex.split('ansible-playbook setup.yml --extra-vars "fs=iozone mode=client"'),
            stdout=PIPE)
  start = False
  try:
    while True:
      l = str(p.stdout.readline(), 'utf-8')
      if 'RETRYING' in l: continue
      if 'Run IOZone test' in l:
        start = True
      if 'localhost' in l:
        start = False
      if start:
        sys.stdout.write(l)
        sys.stdout.flush()
      if not l and p.poll() is not None:
        break
  except KeyboardInterrupt as e:
    p.kill()
    p.terminate()
    raise e


def collect_output(name):
  base_dir = './data'
  output_dir = [d for d in os.listdir(base_dir) if len(d) == 36]
  if len(output_dir) == 0:
    sys.stderr.write('Output directory for %s is not found'%name)
    sys.stderr.flush()
    sys.exit(1)
  os.makedirs('%s/%s/%s'%(base_dir, exp_id, name), exist_ok=True)
  print('Move %s/%s to %s/%s/%s'%(base_dir, output_dir[0], base_dir, exp_id, name))
  shutil.move('%s/%s'%(base_dir, output_dir[0]), '%s/%s/%s'%(base_dir, exp_id, name))


def test_fs():
  try:
    for _ in range(n_repeat):
      clis = shuffle_clients()
      while clis:
        name, params = clis.pop()
        print('Testing %s ...'%name)
        update_client_config(**params)
        run_experiment()
        collect_output(name)
  except KeyboardInterrupt:
    sys.stdout.write('Stopped\n')


def test_scalability():
  zone = [
    dict(name='us-east1-b', start=1, end=1)
  ]
  try:
    for i in range(n_repeat):
      n_parallel = 1
      while n_parallel <= 16:
        print('Parallel #: %d, repeat #: %d'%(n_parallel, i))
        clis = shuffle_clients()
        while clis:
          name, params = clis.pop()
          print('Testing %s ...'%name)
          update_client_config(n_parallel=n_parallel, zone=zone, **params)
          run_experiment()
          collect_output(name)
        n_parallel *= 2
  except KeyboardInterrupt:
    sys.stdout.write('Stopped\n')


if __name__ == '__main__':
  test_scalability()