# -*- coding: utf-8 -*-
"""
  equip.instrument
  ~~~~~~~~~~~~~~~~

  Main interface to handle the instrumentation and run the visitors.

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""
from .prog import Program
from .bytecode import BytecodeObject
from .visitors import MethodVisitor

from .utils.log import logger


class Instrumentation(object):
  """
    Main class for handling the instrumentation. The typical workflow is:
      1. Set the location from the ctor or using the `location` setter
      2. Update options, such as `force-rebuild`
      3. Call `prepare_program` to scan the file system for source/bytecode
      4. Register any `on_enter`/`on_exit` instrumentation callbacks
      5. `apply` the instrumentation using a customer visitor
  """

  #: The list of known options
  KNOWN_OPTIONS = ('force-rebuild',)


  def __init__(self, location=None):
    self.options = {}
    self._location = location
    self.program = None
    self.apply_ran = False
    self.wrapping_code = {
      'on_enter': None,
      'on_exit': None
    }

  def set_option(self, key, value=True):
    """
      Sets one of the options used later one by the instrumentation. The available
      options are listed in `KNOWN_OPTIONS`.

      :param key: The name of the option to set.
      :param value: The value of the option. Defaults to ``True``.
    """
    if key not in Instrumentation.KNOWN_OPTIONS:
      raise Exception('Unknown option `%s`' % key)
    self.options[key] = value


  def get_option(self, key):
    """
      Gets the value of an option. Defaults to ``None``.

      :param key: The name of the option.
    """
    if key not in Instrumentation.KNOWN_OPTIONS:
      raise Exception('Unknown option `%s`' % key)
    return self.options.get(key, None)


  @property
  def location(self):
      """
        The path that contains the bytecode of the application to instrument. The path
        can either be a string or an iterable.
      """
      return self._location

  @location.setter
  def location(self, value):
      self._location = value


  def prepare_program(self):
    """
      Builds the representation of the program, and compiles all source files
      if it's either necessary (e.g., missing bytecode for existing source) or
      if the ``force-rebuild`` option is set.
    """
    self.program = Program(self)
    return self.program is not None


  def apply(self, visitor, rewrite=False):
    """
      Runs the visitor over all matching types (e.g., MethodDeclaration, etc.).

      :param visitor: The instance of the visitor to run over the program.
      :param rewrite: Whether the instrumentation should overwrite the bytecode
                      file (pyc) at the end. Default is `False`.
    """
    self.apply_ran = True
    bytecode_files = self.program.bytecode_files
    for bc_file in bytecode_files:
      self.instrument(visitor, bc_file, rewrite)


  def instrument(self, visitor, bytecode_file, rewrite=False):
    """
      Loads the representation of the bytecode in `bytecode_file`, and apply
      the visitor to the representation.

      :param visitor: The instance of the visitor to run over the representation
                      of the bytecode.
      :param bytecode_file: Absolute path of the file containing the bytecode (pyc).
      :param rewrite: Whether the instrumentation should overwrite the bytecode
                      file (pyc) at the end. Default is `False`.
    """
    logger.debug("File: %s", bytecode_file)
    code = BytecodeObject(bytecode_file)
    code.accept(visitor)

    if rewrite:
      if self.wrapping_code['on_enter']:
        code.add_enter_code(*self.wrapping_code['on_enter'])

      if self.wrapping_code['on_exit']:
        code.add_exit_code(*self.wrapping_code['on_exit'])

      if code.has_changes:
        code.write()


  def on_enter(self, python_code, import_code=None):
    """
      Inserts the ``python_code`` at the beginning of the module inside an if statement. The
      resulting injected code looks like this::

        if __name__ == '__main__':
          python_code

      :param python_code: Python code to inject before the module gets executed (if it's executed
                          under main). The code is not executed if it's not under main.
      :param import_code: Python code that contains the import statements that might be required
                          by the injected ``python_code``. Defaults to None.
    """
    if self.apply_ran:
      raise Exception('on_enter method should be called before `Instrumentation::apply`')
    self.wrapping_code['on_enter'] = (python_code, import_code)


  def on_exit(self, python_code, import_code=None):
    """
      Inserts the ``python_code`` at the end of the module inside an if statement. The
      resulting injected code looks like this::

        if __name__ == '__main__':
          python_code

      :param python_code: Python code to inject after the module gets executed (if it's executed
                          under main). The code is not executed if it's not under main.
      :param import_code: Python code that contains the import statements that might be required
                          by the injected ``python_code``. Defaults to None.
    """
    if self.apply_ran:
      raise Exception('on_exit method should be called before `Instrumentation::apply`')
    self.wrapping_code['on_exit'] = (python_code, import_code)


  def validate(self):
    """
      Debugging info for the instrumented bytecode. Iterates again over all the bytecode
      and dumps the current (instrmented) bytecode.
    """

    class SimpleMethodVisitor(MethodVisitor):
      def __init__(self):
        MethodVisitor.__init__(self)

      def visit(self, methDecl):
        logger.debug("visit methDecl:=%s", methDecl)
        logger.debug("code object := %s", methDecl.code_object)
        logger.debug(get_debug_code_object_info(methDecl.code_object))

        bc = BytecodeObject.get_parsed_code(methDecl.code_object)
        logger.debug("\n%s", show_bytecode(bc))
        logger.debug("End visit")


    for bytecode_file in self.program.bytecode_files:
      code = BytecodeObject(bytecode_file)
      code.parse()
      main_module = code.get_module()
      if not main_module:
        logger.error("Cannot find module for %s", bytecode_file)
        continue
      logger.debug("Tree:\n%s", BytecodeObject.build_tree(main_module))

      logger.debug("Module bytecode:\n%s", show_bytecode(main_module.bytecode))

      # Print the bytecode for each method
      simple_visitor = SimpleMethodVisitor()
      code.accept(simple_visitor)
