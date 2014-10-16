# -*- coding: utf-8 -*-
"""
  Simple Counter
  ~~~~~~~~~~~~~~

  Instrumentation example that gathers method invocation counts
  and dumps the numbers when the program exists, in JSON format.

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""
import sys
from equip import Program, \
                  Instrumentation, \
                  SimpleRewriter, \
                  MethodVisitor
import equip.utils.log as logutils
from equip.utils.log import logger
logutils.enableLogger(to_file='./equip.log')


# Declaration of the code to be injected in various places. This
# code is compiled to bytecode which is then added to the various
# code_objects (e.g., method, etc.) based on what the visitor specifies.
BEFORE_CODE = """
GlobalCounterInst.count(file='{file_name}',
                        class_name='{class_name}',
                        method='{method_name}',
                        lineno={lineno})
"""

# We need to inject a new import statement that contains the GlobalCounterInst
IMPORT_CODE = """
from counter import GlobalCounterInst
"""

ON_ENTER_CODE = """
print "Starting instrumented program"
"""

# When the instrumented code exits, we want to serialize the data
ON_EXIT_CODE = """
GlobalCounterInst.to_json('./data.json')
"""


# The visitor is called for each method in the program (function or method)
class CounterInstrumentationVisitor(MethodVisitor):
  def __init__(self):
    MethodVisitor.__init__(self)

  def visit(self, meth_decl):
    rewriter = SimpleRewriter(meth_decl)

    # Ensure we have imported our `GlobalCounterInst`
    rewriter.insert_import(IMPORT_CODE, module_import=True)

    # This is the main instrumentation code with a callback to
    # `GlobalCounterInst::count`
    rewriter.insert_before(BEFORE_CODE)


HELP_MESSAGE = """
 1. Run counter_instrument.py on the code you want to instrument:
   $ python counter_instrument.py <path/to/code>
 2. Run your original program:
   $ export PYTHONPATH=$PYTHONPATH:/path/to/counter
   $ python start_my_program.pyc
"""

def main(argc, argv):
  if argc < 2:
    print HELP_MESSAGE
    return

  visitor = CounterInstrumentationVisitor()
  instr = Instrumentation(argv[1])
  instr.set_option('force-rebuild')

  if not instr.prepare_program():
    print "[ERROR] Cannot find program code to instrument"
    return

  # Add code at the very beginning of each module (only triggered if __main__ routine)
  instr.on_enter(ON_ENTER_CODE)

  # Add code at the end of each module (only triggered if __main__ routine)
  instr.on_exit(ON_EXIT_CODE)

  # Apply the instrumentation with the visitor, and when a change has been made
  # it will overwrite the pyc file.
  instr.apply(visitor, rewrite=True)


if __name__ == '__main__':
  main(len(sys.argv), sys.argv)
