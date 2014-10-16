import pytest
from testutils import get_co, get_bytecode

import equip
from equip.rewriter.merger import Merger
from equip.bytecode.utils import show_bytecode


INSTR_CODE = """print 'hello'"""


INSTRUMENTED_CODE = """
if foo == 1:
    print "help"

def function():
  %s
  something_else()

if __name__ == '__main__':
  function()
""" % INSTR_CODE


def test_already_merged():
  instrumented = get_bytecode(get_co(INSTRUMENTED_CODE))
  instrument = get_bytecode(get_co(INSTR_CODE))[:-2]
  assert Merger.already_instrumented(instrumented, instrument)


