import pytest
import dis
from testutils import get_co, get_bytecode

from equip import BytecodeObject
from equip.bytecode.utils import show_bytecode
import equip.utils.log as logutils
from equip.utils.log import logger
logutils.enableLogger(to_file='./equip.log')

from equip.analysis import ControlFlow, BasicBlock, CallGraph, DefUse


SIMPLE_PROGRAM = """
import random
import sys

def ask_ok(prompt, retries=4, complaint='Yes or no, please!'):
  while True:
    ok = raw_input(prompt)
    if ok in ('y', 'ye', 'yes'):
      return ask_ok(ok)
    if ok in ('n', 'no', 'nop', 'nope'):
      some_value(some_value(some_value(some_value(1))))
      return False
    retries = retries - 1
    if retries < 0:
      raise IOError('refusenik user')
      print "Never reached"
    print complaint

  if foobar:
    print "whatever"

class Baz:

  class Nested:
    def foo(self):
      self.a = 1
      return self.a

  def __init__(self):
    self.n = Nested()

  def call_me(self, test):
    print test

def other():
  baz = Baz()
  baz.call_me()
  baz.n.foo()

  b = baz
  b.call_me()

  a(1, 2)


if __name__ == '__main__':
  main()
"""

def test_callgraph():
  co_simple = get_co(SIMPLE_PROGRAM)
  assert co_simple is not None

  bytecode_object = BytecodeObject('<string>')
  bytecode_object.parse_code(co_simple)

  callgraph = CallGraph()
  callgraph.process(bytecode_object.main_module)


CALL_STRUCTURES_CASE = """
func(1, 2, foo=bar, baz=biz, *foo_list, **boz_dct)
func(*baz_list)
func(**baz_dct)
func(*baz_list, **baz_dct)
func(1, *baz_list)
func(func(func(func())))
"""

def test_parse_calls():
  co_simple = get_co(CALL_STRUCTURES_CASE)
  assert co_simple is not None

  bytecode_object = BytecodeObject('<string>')
  bytecode_object.parse_code(co_simple)

  callgraph = CallGraph()
  callgraph.process(bytecode_object.main_module)
  block_calls = callgraph.block_calls

  all_names = set()
  all_calls = set()

  for block in block_calls:
    for index in block_calls[block]:
      all_calls.add(index)
      all_names.add('.'.join(block_calls[block][index]))

  assert len(all_names) == 1
  assert len(all_calls) == 9



