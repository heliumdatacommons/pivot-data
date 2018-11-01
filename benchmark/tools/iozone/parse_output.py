#!/usr/bin/env python3

import os
import json


field_names = ('file_size', 'reclen', 'write', 'rewrite', 'read', 'reread', 'random_read',
               'random_write', 'bkwd_read', 'record_rewrite', 'stride_read', 'fwrite', 'frewrite',
               'fread', 'freread')


def parse_output():
  start = False
  output = []
  output_fn = '/data/stats-%s.txt'%os.environ['CLIENT_ID']
  with open(output_fn) as f:
    for l in f.readlines():
      if 'reclen' in l:
        start = True
        continue
      if not start: continue
      if len(l.split()) < 14: break
      output += [{field_names[i]: int(f) for i, f in enumerate(l.split())}]
  if len(output) > 0:
    json.dump(output, open('/data/stats-%s.json' % os.environ['CLIENT_ID'], 'w'), indent=2)
  os.remove(output_fn)


if __name__ == '__main__':
  parse_output()

