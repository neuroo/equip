import pytest
from itertools import tee, izip
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
      elif n == 2 or n in (1,2) or n / 3 == 1:
        continue
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

def jump_no_absolute(foo):
  if foo.bar == 1:
    if foo.baz == 2:
      if foo.buzz == 3:
        return some_value(foo)
      else:
        return other_value(foo)

if __name__ == '__main__':
  main()
"""


def test_cflow1():
  co_simple = get_co(SIMPLE_PROGRAM)
  assert co_simple is not None

  bytecode_object = BytecodeObject('<string>')
  bytecode_object.parse_code(co_simple)

  assert len(bytecode_object.declarations) == 11

  for decl in bytecode_object.declarations:
    cflow = ControlFlow(decl)
    assert cflow.blocks is not None
    assert len(cflow.graph.roots()) == 1
    assert len(cflow.dominators.dom) > 0
    cflow.block_constraints is not None
    for block in cflow.block_constraints:
      cstr = cflow.block_constraints[block]
      assert cstr.tree is not None
      logger.debug("Constraint: %s", cstr)
    cdg = cflow.control_dependence


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


CONDITION_CASE = """
if a + b + c < 2:
  print 'foo'
elif ((a & 0xff != 0) and 2 + something(foobar ** 2) + 1 != 0) or 1 == 2:
  print 'bar'
"""


def test_conditions():
  logger.debug("test_conditions")
  co_simple = get_co(CONDITION_CASE)
  assert co_simple is not None

  bytecode_object = BytecodeObject('<string>')
  bytecode_object.parse_code(co_simple)

  for decl in bytecode_object.declarations:
    cflow = ControlFlow(decl)
    cflow.block_constraints


CONSTRAINT_EQ_CASE = """
def f1():
  if a > 0 and a > 0:
    print 'dood'

def f2():
  if a + b > 0 and b + a > 0:
    print 'dood'

def f3():
  # Note that this fails if we remove the parens around b/2 since
  # the comparison operator doesn't get the distributivity (only the
  # commutativity of operators)
  if a * (b * (1/2)) > 0 and a * ((1/2) * b) > 0:
    print 'dood'
"""


def get_pairs(iterable):
  a, b = tee(iterable)
  next(b, None)
  return izip(a, b)


def test_constraint_equivalence():
  logger.debug("test_conditions")
  co_simple = get_co(CONSTRAINT_EQ_CASE)
  assert co_simple is not None

  bytecode_object = BytecodeObject('<string>')
  bytecode_object.parse_code(co_simple)

  for decl in bytecode_object.declarations:
    cflow = ControlFlow(decl)
    all_constraints = list()
    for block in cflow.block_constraints:
      logger.debug("Cstr: %s", cflow.block_constraints[block].tree)
      all_constraints.append(cflow.block_constraints[block].tree)

    for cstr1, cstr2 in get_pairs(all_constraints):
      assert cstr1 == cstr2


LIST_COMP_CASE = """
def f1(a):
  if a == 1:
    lst = [d for d in a]
    return lst
  else:
    lst1 = [(foo, bar) for foo, bar in a.getValues() if foo != 'some' if bar != 'ddd' if bar != 'ddd' if bar != 'ddd'] # list comp
    lst2 = ((foo, bar) for foo, bar in a.getValues() if foo != 'some') # gen
    pyt = ((x, y, z) for z in integers()   \
                     for y in xrange(1, z) \
                     for x in range(1, y)  \
                     if x*x + y*y == z*z)
    print pyt
  return []
"""


def test_list_comprehension():
  logger.debug("test_list_comprehension")
  co_simple = get_co(LIST_COMP_CASE)
  assert co_simple is not None

  bytecode_object = BytecodeObject('<string>')
  bytecode_object.parse_code(co_simple)

  for decl in bytecode_object.declarations:
    cflow = ControlFlow(decl)

    for block in cflow.blocks:
      for stmt in block.statements:
        if stmt.native is not None:
          logger.debug("%s", stmt)
