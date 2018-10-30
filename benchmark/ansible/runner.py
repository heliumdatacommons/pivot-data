import os
import sys
import yaml
import shlex
import shutil
import numpy as np

from subprocess import Popen, PIPE, STDOUT

exp_id = '8362791176069c95cff2d575b7a5f58ec7fc3ed4'
# exp_id = 'd0e4c0aef2b9b26921b075fa32e445526c909f51'
n_repeat = 15

clients = {
  'rbd': dict(host='10.52.100.16', type='nfs', dir='/', opts='vers=4'),
  'cephfs': dict(host='10.52.100.12', type='ceph', dir='/', opts='mds_namespace=alpha'),
  'nfsv4': dict(host='10.52.100.22', type='nfs', dir='/', opts='vers=4'),
  'ganesha': dict(host='10.52.100.23', type='nfs', dir='/', opts='vers=4'),
  'gfganesha': dict(host='10.52.100.19', type='nfs', dir='/data', opts='vers=4'),
  'rbdganesha': dict(host='10.52.100.3', type='nfs', dir='/', opts='vers=4'),
}


def update_config(host, type, dir, opts):
  fn = 'group_vars/all.yml'
  cfg = yaml.load(open(fn))
  cfg['client'].update(host=host, type=type, dir=dir, opts=opts)
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
  try:
    while True:
      l = p.stdout.readline()
      sys.stdout.write(l.decode('utf-8'))
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
    sys.exit(1)
  os.makedirs('%s/%s/%s'%(base_dir, exp_id, name), exist_ok=True)
  print('Move %s/%s to %s/%s/%s'%(base_dir, output_dir[0], base_dir, exp_id, name))
  shutil.move('%s/%s'%(base_dir, output_dir[0]), '%s/%s/%s'%(base_dir, exp_id, name))


if __name__ == '__main__':
  try:
    for _ in range(n_repeat):
      clis = shuffle_clients()
      while clis:
        name, params = clis.pop()
        print('Testing %s ...'%name)
        update_config(**params)
        run_experiment()
        collect_output(name)
  except KeyboardInterrupt:
    sys.stdout.write('Stopped\n')