Getting Started
===============

equip has a simple interface that contains a handful of important classes to work with:

 * Instrument
 * SimpleRewriter
 * MethodVisitor


Instrument
----------
Main interface for the instrumentation. It triggers the conversion from the bytecode to
the internal representation, as well as executing the visitors and writing back the resulting
bytecode.

The workflow of ``Instrument`` requires the following steps:

 1. Pass the location (or locations) to the Instrument::

      instr.location = ['path/to/module', 'path/to/other/module']

 2. Ask ``Instrument`` to prepare the program by compiling the sources (if necessary or requested)
    and creating a list of bytecode files that can be instrumented::

      if not instr.prepare_program():
        raise Exception('Error while compiling the code...')

 3. Apply the visitor on all bytecode files and persist the new bytecode::

      instr.apply(my_visitor, rewrite=True)


The compilation of the program is not performed by default as the program might already be compiled,
and the bytecode ready to consume. If however, we want to force rebuilding the bytecode for the
entire application, we can set the force-rebuild option between step 1 and 2::

  instr.set_option('force-rebuild')


Visitors
--------
The ``Instrument`` creates a representation for each pyc file that contains different
``Declaration`` objects. A visitor can be created to iterate over these ``Declaration``.

The most commonly used visitor is the ``MethodVisitor`` that is triggered over all method
declarations found in the bytecode.

Here's an example of a visitor that prints the start and end line for each method::

  class MethodLinesVisitor(MethodVisitor):
    def __init__(self):
      MethodVisitor.__init__(self)

    def visit(self, meth_decl):
      print "Method %s: start=%d, end=%d" \
            %  (meth_decl.method_name, meth_decl.start_lineno, meth_decl.end_lineno)



SimpleRewriter
--------------
Handles the insertion of bytecode, and generation of proper bytecode. The rewriter allows for
multiple operations such as:

  * Insert generic bytecode
  * Insert import statements
  * Insert on_enter/on_exit callbacks

The rewriter is called from within a visitor or any other way to get a particular ``Declaration``.
It consumes the ``Declaration`` and allows for inserting bytecode at any desired point in the
original bytecode.

For example, we can add create an instrumentation to insert for all returns in a method::

  ON_AFTER = """
  print "Exit {method_name}, return value := %s" % repr({return_value})
  """

  class ReturnValuesVisitor(MethodVisitor):
    def __init__(self):
      MethodVisitor.__init__(self)

    def visit(self, meth_decl):
      rewriter = SimpleRewriter(meth_decl)
      rewriter.insert_after(ON_AFTER)

Note that the ``Instrument`` is currently responsible for applying the changes, which means
serializing the declarations of the current bytecode.
