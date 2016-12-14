import pytest
from testutils import get_co, get_bytecode

from equip import BytecodeObject
from equip.bytecode import MethodDeclaration, TypeDeclaration, ModuleDeclaration
from equip.bytecode.utils import show_bytecode, iter_decl


SIMPLE_PROGRAM = """
import random
import sys

a = lambda x, y: x + y

class B: pass

class Foo(object):
  def __init__(self):
    pass

class Bar(Foo):
  def __init__(self):
    pass

KEY = 'something'
VALUE = __name__

def some_value(i):
  return i - 1

def while_loop(data, start):
  return -1

def main():
  print "%30s: %30s" % (KEY, VALUE)

b, c = lambda z: z + 1, lambda c: c ** 2

if __name__ == '__main__':
  main()
"""


def test_decl_1():
  co_simple = get_co(SIMPLE_PROGRAM)
  assert co_simple is not None

  bytecode_object = BytecodeObject('<string>')
  bytecode_object.parse_code(co_simple)

  assert len(bytecode_object.declarations) == 12

  assert len([k for k in bytecode_object.declarations if isinstance(k, MethodDeclaration) and k.is_lambda]) == 3

  assert len([k for k in bytecode_object.declarations if isinstance(k, TypeDeclaration)]) == 3

  assert len([k for k in bytecode_object.declarations if isinstance(k, ModuleDeclaration)]) == 1

  module = bytecode_object.main_module
  assert len(module.imports) == 2



NESTED_METHS_PROGRAM = """
mult = lambda m: lambda n: lambda f: lambda x: m(n(f))(x)

reduce(operator.or_,
       map(lambda y: reduce(operator.or_,
                            map(lambda x: x[0] == y,
                            other_bucket)),
           bucket,
           footers))

def one_method():
  a = lambda x: x ** 2
  b = (lambda z: (lambda a: a + z))

  def nested_1():
    c = lambda d: d ** 3

    def nested_1_2():
      print "a", c(2)
"""


def test_nested_methods_lambdas():
  co_simple = get_co(NESTED_METHS_PROGRAM)
  assert co_simple is not None

  bytecode_object = BytecodeObject('<string>')
  bytecode_object.parse_code(co_simple)

  assert len(bytecode_object.declarations) == 14

  nested_1_decl = bytecode_object.get_decl(method_name='nested_1')
  assert nested_1_decl is not None
  assert len(nested_1_decl.children) == 2

  one_method_decl = bytecode_object.get_decl(method_name='one_method')
  assert one_method_decl is not None
  assert len(one_method_decl.children) == 3

  nested_1_2_decl = bytecode_object.get_decl(method_name='nested_1_2')
  assert nested_1_2_decl is not None
  assert len(nested_1_2_decl.children) == 0


INHERITANCE_CASE = """
class Base:
  pass

class OtherBase:
  pass

def gen(*args):
  pass

@gen
@gen
@gen
@gen
class NewBase(object):
  pass

class Child1(Base):
  pass

class Child2(Base, OtherBase, NewBase):
  pass

"""
def test_inheritance():
  co_simple = get_co(INHERITANCE_CASE)
  assert co_simple is not None
  bytecode_object = BytecodeObject('<string>')
  bytecode_object.parse_code(co_simple)

  TEST_CASE = {
    'Base': 0,
    'OtherBase': 0,
    'NewBase': 0,
    'Child1': 1,
    'Child2': 3
  }

  for decl in iter_decl(bytecode_object.main_module):
    if not isinstance(decl, TypeDeclaration):
      continue
      assert len(decl.superclasses) == TEST_CASE[decl.type_name]
