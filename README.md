[![Build Status](https://travis-ci.org/neuroo/equip.svg?branch=master)](https://travis-ci.org/neuroo/equip) [![Documentation Status](https://readthedocs.org/projects/equip/badge/?version=latest)](https://readthedocs.org/projects/equip/?badge=latest)

# equip: Python Bytecode Instrumentation

equip is a small library that helps with Python bytecode instrumentation. Its API
is designed to be small and flexible to enable a wide range of possible instrumentations.

The instrumentation is designed around the injection of bytecode inside the
bytecode of the program to be instrumented. However, the developer does not need to know
anything about the Python bytecode since the injected code is Python source.

## Installation
The package can be installed with pip for the latest release:
```bash
$ pip install equip
```

Or you can get/install the latest development version:
```bash
$ git clone https://github.com/neuroo/equip.git
$ cd equip
$ python setup.py install
```

## Documentation
The documentation is available on http://equip.readthedocs.org

## Simplest Example

The following example shows how to write a simple instrumentation tool that will print all
method called in the program, along with its arguments:

```python
  import sys
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
```

This program requires the path to the program to instrument, and will compile the source
to generate the bytecode to instrument. All bytecode will be loaded into a representation,
and the `MethodInstr` visitor will be called on all method declarations.

When a change is required (i.e., the code actually needs to be instrumented), the
`Instrumentation` will overwrite the `pyc` file.

Running the instrumented program afterwards does not require anything but executing it as you
would usually do. If the injected code has external dependencies, you can simply modify the
`PYTHONPATH` to point to the required modules.

A more realistic example can be found in the examples:
  * [Call counters](https://github.com/neuroo/equip/blob/master/examples/counter/counter_instrument.py): Instrument a program and record calls for each method during its execution. The output is then serialized to JSON.


## Versioning and Experimental Status
The current status of equip should be considered experimental. There is much more tests
to be written and code cleanup to be made before equip can be considered as reliable.

When it is reliable, it will be bumped to version 1.0.

## Current Capabilities of Equip
The API of equip is fairly high level and it's possible not to use the simple `Instrument` interface
in order to manually retrieve `Declaration` found in the bytecode. Then rewrite them manually. A 
`BytecodeVisitor` is also provided to iterate over all the bytecode (however, no rewriter is currently
available to easily append one instruction at a time).

Another part of the API in equip allow for reasoning about the python bytecode (currently, with control
flow analysis).


### Bytecode Injection
The current way to inject custom code in the original bytecode is handled by the [`SimpleRewriter`](http://equip.readthedocs.org/en/latest/equip.rewriter.html#equip.rewriter.simple.SimpleRewriter).
It allows for injections in multiple parts:
 * BEFORE: before any other bytecode
 * AFTER: just before each `RETURN_VALUE`
 * LINENO: when a given line number is encountered
 * MODULE_ENTER: at the very beginning of a module (wrapped in a `if __name__ == '__main__'`)
 * MODULE_EXIT: at the very end of a module (wrapped in a `if __name__ == '__main__'`)

Specific methods are available to handle these injection, for which the first step is to process the code to be
injected to replace the templated values (e.g., `{return_value}`, `{arguments}`, etc.) and then compile the code.

The compiled code is what will be injected in the original bytecode.

Since the code might have external dependencies, it is possible to add new import statements (which are written
in the module), using [`SimpleRewriter.insert_import`](http://equip.readthedocs.org/en/latest/equip.rewriter.html#equip.rewriter.simple.SimpleRewriter.insert_import)

### Bytecode Analysis
For smarter instrumentation, you often need to perform lightweight analysis of the bytecode. equip provides 
some capabilities in this domain with:
 * Construction of the [`ControlFlow`](http://equip.readthedocs.org/en/latest/equip.analysis.html#equip.analysis.flow.ControlFlow) graph (associated with one `Declaration`)
 * Dominance properties are also computed (dominator tree, post-dominators, dominance frontier) and provided by the [`DominatorTree`](http://equip.readthedocs.org/en/latest/equip.analysis.graph.html#equip.analysis.graph.dominators.DominatorTree) utility
 * Traversals to help with searching the CFG

 
 

