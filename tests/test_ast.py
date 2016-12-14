import pytest
from itertools import tee, izip
from testutils import get_co, get_bytecode

from equip import BytecodeObject
from equip.bytecode.utils import show_bytecode
from equip.analysis.ast.utils import dump
import equip.utils.log as logutils
from equip.utils.log import logger
logutils.enableLogger(to_file='./equip.log')

from equip.analysis import ControlFlow, BasicBlock

import ast

SIMPLE_PROGRAM = """
import random
import sys

a = lambda x, y: x + (y if foo == 'bar' else x)

def some_value(i):
  if (i % 2) == 0:
    print "even",
  elif foobar:
    print "whatever"
  else:
    print "odd",

  for n in range(2, 10):
    for x in range(2, n):
      if n % x == 0:
        print n, 'equals', x, '*', n/x
        break
      elif n == 2 or n in (1,2) or n / 3 == 1:
        continue
      print "foobar"
    else:
      # loop fell through without finding a factor
      print n, 'is a prime number'

  print "number: %d" % i
  print >> sys.stderr, 'whatever string to STDERR'
  print a.b.zoo, a.b, foo()

  print {1: 2, 3: 4, 'foo': 'bar', 'zoo': {11: {12: 13}}}, {}

  func(foo=bar)
  func(foo=bar, baz=booz)
  func(1, 2, foo=bar, baz=biz, *foo_list, **boz_dct)
  func(*baz_list)
  func(**baz_dct)
  func(*baz_list, **baz_dct)
  func(1, *baz_list)
  func(func(func(func())))

  a.b.z.d(1, 2, (1, 2), {None:None, 1:2, 3:4})

  a = b = 1
  e = f = g = 2
  e = f = g.goo().bar().test = foo.test.zz[1].some()
  h = e
  a = b = c = d = 2
  a, b, c, d = foobarunpack()
  a, b = foob(), boof()   # <=> a = foob() && b = boof()
  a, b, c = foob(), boof() # <=> a, b, c = foob() ; boof()
  a, b = 1, 2
  a, b = c, d
  a, b, c = d, e, f
  a, b, c, d = e, foo(foo(bar())), g, h
  a, b, c, d = 1, d, e, f
  a += 1
  a = 1

  zb.d.e.f.ghhhh, za, zd = xb, xa, xd

  a['1'] = dddd
  a[getIndex()] = dddd
  a[1 + 2 + 4] = dddd
  a[1 + 2 + foo()] = dddd
  a[baz() + 2 + foo()] = dddd

  a[start:end:step] = foo()
  a[start:end] = foo()
  a[start:] = foo()
  a[:end] = foo()
  a[:] = foo()
  a[::-1] = foo()
  a[::-9] = foo()

  del a
  del a, b, c, d
  del a.b.c
  del foo['bar']
  del a[1:]
  del a[1:1]
  del a[1:1:1]
  del a[::-9]

  a = a if op not in foo else bar
  a = [(a[1], a[2]) for a in bar if bar != None]

  return i - 1


def ask_ok(prompt, retries=4, complaint='Yes or no, please!'):
  while True:
    ok = raw_input(prompt)
    if ok in ('y', 'ye', 'yes'):
      return True
    if ok in ('n', 'no', 'nop', 'nope'):
      return False
      print False
    retries = retries - 1
    if retries < 0:
      raise IOError('refusenik user')
      print "Never reached"
    print complaint

    if isinstance(b, string):
      print 'b is a string'

  if foobar:
    print "whatever"


def with_stmt(something):
  with open('output.txt', 'w') as f:
    f.write('Hi there!')

def exception_tests():
  try:
    fd = open('something')
  except SomeException, ex:
    print "SomeException"
  except Exception, ex:
    print "Last Exception"
  finally:
    print "Finally"

def while_loop(data, start):
  while start < len(data):
    print start
    start += 1
    if 0 > start > 10:
      return -1

def test_conditions():
  global FOOBAR

  if (a + b + something(FOOBAR)) == 0:
    print foo

def main():
  for i in range(1, random.randint()):
    print some_value(i)

  print "Call stats:"
  items =  sys.callstats().items()
  items = [(value, key) for key, value in items]
  items.sort()
  items.reverse()
  for value,key in items:
    print "%30s: %30s"%(key, value)


def return_Stmts(i):
  if i == 1:
    return 1
  elif i == 2:
    return 2

  print "This is something else"


if __name__ == '__main__':
  main()
"""

def test_ast():
  co_simple = get_co(SIMPLE_PROGRAM)
  assert co_simple is not None

  bytecode_object = BytecodeObject('<string>')
  bytecode_object.parse_code(co_simple)

  assert len(bytecode_object.declarations) == 10

  for decl in bytecode_object.declarations:
    cflow = ControlFlow(decl)
    assert cflow.blocks is not None

    for block in cflow.blocks:
      for stmt in block.statements:
        if stmt.native is not None:
          logger.debug("%s", stmt)
          logger.debug("%s", dump(stmt.native))

