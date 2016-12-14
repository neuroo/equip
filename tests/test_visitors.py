import pytest
from testutils import get_co, get_bytecode

from equip import BytecodeObject, BlockVisitor
from equip.bytecode import MethodDeclaration, TypeDeclaration, ModuleDeclaration
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


def test_block_visitor():
  co_simple = get_co(SIMPLE_PROGRAM)
  assert co_simple is not None

  bytecode_object = BytecodeObject('<string>')
  bytecode_object.parse_code(co_simple)

  class BlockPrinterVisitor(BlockVisitor):
    def __init__(self):
      BlockVisitor.__init__(self)

    def new_control_flow(self):
      logger.debug("Received new CFG: %s", self.control_flow)

    def visit(self, block):
      logger.debug("Visiting block: %s", block)
      logger.debug('\n' + show_bytecode(block.bytecode))

  visitor = BlockPrinterVisitor()
  bytecode_object.accept(visitor)




