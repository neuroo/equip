.. equip documentation master file, created by
   sphinx-quickstart on Tue Oct 14 11:07:39 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to equip's documentation!
=================================

equip is a small library that helps with Python bytecode instrumentation. Its API
is designed to be small and flexible to enable a wide range of possible instrumentations.

The instrumentation is designed around the injection of bytecode inside the
bytecode of the program to be instrumented. However, the developer does not need to know
anything about the Python bytecode.

The following example shows how to write a simple instrumentation tool that will print all
method called in the program, along with its arguments::

  import sys
  import equip
  from equip import Instrumentation, MethodVisitor, SimpleRewriter

  BEFORE_CODE = """
  print ">> START"
  print "[CALL] {file_name}::{method_name}:{lineno}", {arguments}
  print "<< END"
  """

  class MethodInstr(MethodVisitor):
    def __init__(self):
      MethodVisitor.__init__(self)

    def visit(self, meth_decl):
      rewriter = SimpleRewriter(meth_decl)
      rewriter.insert_before(BEFORE_CODE)

  instr_visitor = MethodInstr()
  instr = Instrumentation(sys.argv[1])
  if not instr.prepare_program():
    return
  instr.apply(instr_visitor, rewrite=True)

This program requires the path to the program to instrument, and will compile the source
to generate the bytecode to instrument. All bytecode will be loaded into its representation,
and the ``MethodInstr`` visitor will be called on all method declarations.

When a change is required (i.e., the code actually needs to be instrumented), the
``Instrumentation`` will overwrite the ``pyc`` file.

Running the instrumented program afterwards does not require anything but executing it as you
would usually do. If the injected code has external dependencies, you can simply modify the
``PYTHONPATH`` to point to the required modules.

Contents:

.. toctree::
   :maxdepth: 2

   installation
   gettingstarted
   examples
   api


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

