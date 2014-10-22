import pytest
from testutils import get_co, get_bytecode

from equip import BytecodeObject
from equip.bytecode.utils import show_bytecode
import equip.utils.log as logutils
from equip.utils.log import logger
logutils.enableLogger(to_file='./equip.log')

from equip.analysis import ControlFlow, BasicBlock


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
      print "foobar"
    else:
      # loop fell through without finding a factor
      print n, 'is a prime number'

  print "number: %d" % i
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
    if start > 10:
      return -1

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

def test_cflow1():
  co_simple = get_co(SIMPLE_PROGRAM)
  assert co_simple is not None

  bytecode_object = BytecodeObject('<string>')
  bytecode_object.parse_code(co_simple)

  assert len(bytecode_object.declarations) == 9

  for decl in bytecode_object.declarations:
    cflow = ControlFlow(decl)
    assert cflow.blocks is not None
    assert len(cflow.dominators.dom) > 0


WHILE_CASE = """
while i < length:
  i += 1
  print i
"""
def test_while_loop():
  co_simple = get_co(WHILE_CASE)
  assert co_simple is not None

  bytecode_object = BytecodeObject('<string>')
  bytecode_object.parse_code(co_simple)

  assert len(bytecode_object.declarations) == 1

  for decl in bytecode_object.declarations:
    cflow = ControlFlow(decl)
    assert cflow.blocks is not None
    assert len(cflow.dominators.dom) > 0

IF_STMTS_CASE = """
if i == 1:
  print 1
elif i == 2:
  print 2
elif i % 0 == 1:
  print 'elif'
else:
  print 'final-case'
"""
def test_if_statements():
  co_simple = get_co(IF_STMTS_CASE)
  assert co_simple is not None

  bytecode_object = BytecodeObject('<string>')
  bytecode_object.parse_code(co_simple)

  assert len(bytecode_object.declarations) == 1

  for decl in bytecode_object.declarations:
    cflow = ControlFlow(decl)
    assert cflow.blocks is not None
    assert len(cflow.dominators.dom) > 0

LOOP_BREAK_CASE = """
def func():
  while i < length:
    if i % 2 == 0:
      break
    for j in range(0, 10):
      k = 0
      for k in range(0, 10):
        l = 0
        for l in range(0, 10):
          print j, k, l
          if l == 2:
            break
          elif l == 3:
            return
        print "end-l-loop"
        if k == 2:
          break
      print "end-k-loop"
    print "end-j-loop"

  print "Final"
"""
def test_loop_breaks():
  logger.debug("test_loop_breaks")
  co_simple = get_co(LOOP_BREAK_CASE)
  assert co_simple is not None

  bytecode_object = BytecodeObject('<string>')
  bytecode_object.parse_code(co_simple)

  assert len(bytecode_object.declarations) == 2

  for decl in bytecode_object.declarations:
    cflow = ControlFlow(decl)
    assert cflow.blocks is not None
    assert len(cflow.dominators.dom) > 0
