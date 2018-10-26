#!/usr/bin/env python3

import os
import sys
import json


field_names = ('file_size', 'reclen', 'write', 'rewrite', 'read', 'reread', 'random_read',
               'random_write', 'bkwd_read', 'record_rewrite', 'stride_read', 'fwrite', 'frewrite',
               'fread', 'freread')


def read_stdin():
  while True:
    yield sys.stdin.readline().strip()


def parse_line(l):
  res = {field_names[i]: int(f) for i, f in enumerate(l.split())}
  sys.stdout.write(json.dumps(res) + '\n')
  sys.stdout.flush()
  return res


def filter_input():
  start = False
  for l in read_stdin():
    if 'reclen' in l:
      start = True
      continue
    if not start: continue
    if len(l.split()) < 14: break
    write(parse_line(l))


def write(l):
  fn = '/data/stats-%s.json'%os.environ['CLIENT_ID']
  try:
    output = json.load(open(fn))
  except:
    output = []
  output.append(l)
  json.dump(output, open(fn, 'w+'), indent=2)


if __name__ == '__main__':
  filter_input()
