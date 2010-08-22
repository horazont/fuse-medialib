#!/usr/bin/python

import sys
input = open("/tmp/debug", "r")
try:
  while True:
    sys.stdout.write(input.read(2))
finally:
  input.close()
