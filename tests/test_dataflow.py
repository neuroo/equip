import pytest
import dis
from testutils import get_co, get_bytecode

from equip import BytecodeObject
from equip.bytecode.utils import show_bytecode
import equip.utils.log as logutils
from equip.utils.log import logger
logutils.enableLogger(to_file='./equip.log')

from equip.analysis import ControlFlow, BasicBlock, CallGraph, DefUse, TypeInference


DEF_USE_SIMPLE = """
b.bazz.z()
b = foo()
c = b.result
b.bazz.z = foobar
a = 2
a = 1
if (a < 2 and a >= 1) or b == 1:
  print a
  a = 3
else:
  a = 5
print a
"""

def test_def_use():
  co_simple = get_co(DEF_USE_SIMPLE)
  assert co_simple is not None

  bytecode_object = BytecodeObject('<string>')
  bytecode_object.parse_code(co_simple)
  cfg = ControlFlow(bytecode_object.main_module)
  def_use = DefUse(cfg)



SIMPLE_TYPES_CASE = """
a = 1
b.z.a = a
b[0] = c
b[0]['4545'] = dd
if a == 0:
  a = None
  b.d.a = a
  print a
else:
  if isinstance(b, basestring):
    print "b is a string"
  elif type(b) == type(u'f'):
    print "b is a unicode string"
"""
def test_simple_types():
  co_simple = get_co(SIMPLE_TYPES_CASE)
  assert co_simple is not None

  bytecode_object = BytecodeObject('<string>')
  bytecode_object.parse_code(co_simple)
  cfg = ControlFlow(bytecode_object.main_module)
  types = TypeInference(cfg)
