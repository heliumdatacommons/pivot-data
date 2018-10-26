import sys


def read_stdin():
  return [l.strip() for l in sys.stdin.readlines()]


def filter_input(lines):
  res, start = [], False
  for l in lines:
    if 'reclen' in l:
      start = True
      continue
    if not start: continue
    if 'iozone test complete.' in l:
      break
    res += [l]
  return res


if __name__ == '__main__':
  lines = read_stdin()
  values = filter_input(lines)
  print(values)
