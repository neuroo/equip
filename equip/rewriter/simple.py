# -*- coding: utf-8 -*-
"""
  equip.rewriter.simple
  ~~~~~~~~~~~~~~~~~~~~~

  A simplified interface (yet the main one) to handle the injection
  of instrumentation code.

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""
import os
import copy

from ..utils.log import logger
from ..bytecode.decl import ModuleDeclaration, \
                            MethodDeclaration, \
                            TypeDeclaration
from ..bytecode.code import BytecodeObject
from ..bytecode.utils import show_bytecode, \
                             get_debug_code_object_info

from .merger import Merger, RETURN_CANARY_NAME, LOAD_GLOBAL


# A global tracking what file we added the imports to. This should be refactored
# and we should inspect the module/method for imports.
GLOBAL_IMPORTS_ADDED = set()


EXIT_ENTER_CODE_TEMPLATE = """
if __name__ == '__main__':
%s
"""

class SimpleRewriter(object):
  """
    The current main rewriter that works for one ``Declaration`` object. Using this
    rewriter will modify the given declaration object by possibly replacing all of
    its associated code object.
  """

  #: List of the parameters that can be used for formatting the code
  #: to inject.
  #: The values are:
  #:
  #: * ``method_name``: The name of the method that is being called.
  #:
  #: * ``lineno``: The start line number of the declaration object being
  #:               instrumented.
  #:
  #: * ``file_name``: The file name of the current module.
  #:
  #: * ``class_name``: The name of the class a method belongs to.
  #:
  KNOWN_FIELDS = ('method_name', 'lineno', 'file_name', 'class_name',
                  'arg0', 'arg1', 'arg2', 'arg3', 'arg4',
                  'arg5', 'arg6', 'arg7', 'arg8', 'arg9',
                  'arg10', 'arg11', 'arg12', 'arg13', 'arg14',
                  'arguments', 'return_value')


  def __init__(self, decl):
    self.decl = decl
    self.original_decl = copy.deepcopy(self.decl)

    self.module = None
    if isinstance(self.module, ModuleDeclaration):
      self.module = self.decl
    else:
      self.module = self.decl.parent_module

    self.import_lives = set()


  def insert_before(self, python_code):
    """
      Insert code at the beginning of the method's body.

      The submitted code can be formatted using ``fields`` declared in ``KNOWN_FIELDS``.
      Since ``string.format`` is used once the values are dumped, the injected code should
      be property structured.

      :param python_code: The python code to be formatted, compiled, and inserted
                          at the beginning of the method body.
    """
    if not isinstance(self.decl, MethodDeclaration):
      raise TypeError('Can only insert before/after in a method')
    return self.insert_generic(python_code, location=Merger.BEFORE)


  def insert_after(self, python_code):
    """
      Insert code at each `RETURN_VALUE` opcode. See `insert_before`.
    """
    if not isinstance(self.decl, MethodDeclaration):
      raise TypeError('Can only insert before/after in a method')
    return self.insert_generic(python_code, location=Merger.AFTER)


  def insert_generic(self, python_code, location=Merger.UNKNOWN, \
                     ins_lineno=-1, ins_offset=-1, ins_module=False, ins_import=False):
    """
      Generic code injection utils. It first formats the supplied ``python_code``,
      compiles it to get the `code_object`, and merge this new `code_object` with
      the one of the current declaration object (``decl``). The insertion is done by
      the ``Merger``.

      When the injection is done, this method will go and recursively update all
      references to the old `code_object` in the parents (when a parent changes, it is
      as well updated and its new ``code_object`` propagated upwards). This process is
      required as Python's code objects are nested in parent's code objects, and they
      are all read-only. This process breaks any references that were hold on previously
      used code objects (e.g., don't do that when the instrumented code is running).

      :param python_code: The code to be formatted and inserted.
      :param location: The kind of insertion to perform.
      :param ins_lineno: When an insertion should occur at one given line of code,
                         use this parameter. Defaults to -1.
      :param ins_offset: When an insertion should occur at one given bytecode offset,
                         use this parameter. Defaults to -1.
      :param ins_module: Specify the code insertion should happen in the module
                         itself and not the current declaration.
      :param ins_import: True of the method is called for inserting an import statement.
    """

    target_decl = self.decl if not ins_module else self.module
    original_decl = self.original_decl
    if ins_module and not isinstance(original_decl, ModuleDeclaration):
      original_decl = original_decl.parent_module

    formatted_code = SimpleRewriter.format_code(target_decl, python_code, location)
    injected_co = SimpleRewriter.get_code_object(formatted_code)

    if ins_import:
      # Parse the import statement to extract the imported names.
      bc_import = BytecodeObject.get_parsed_code(injected_co)
      import_stmts = BytecodeObject.get_imports_from_bytecode(injected_co, bc_import)
      for import_stmt in import_stmts:
        self.import_lives = self.import_lives | import_stmt.live_names

    self.inspect_all_globals()

    working_co = target_decl.code_object

    new_co = Merger.merge(working_co,
                          injected_co,
                          location,
                          ins_lineno,
                          ins_offset,
                          self.import_lives)
    if not new_co:
      return self

    original_co = target_decl.code_object
    target_decl.code_object = new_co
    target_decl.has_changes = True

    # Recursively apply this to the parent cos
    parent = target_decl.parent
    original_parent = original_decl.parent

    while parent is not None:
      # inspect the parent cos and update the consts for
      # the original to the current sub-CO
      parent.update_nested_code_object(original_co, new_co)
      original_co = original_parent.code_object
      new_co = parent.code_object
      original_parent = original_parent.parent
      parent = parent.parent

    return self


  def insert_import(self, import_code, module_import=True):
    """
      Insert an import statement in the current bytecode. The import is added
      in front of every other imports.
    """
    logger.debug("Insert import on: %s", self.decl)

    if not module_import:
      return self.insert_generic(import_code, location=Merger.BEFORE, ins_import=True)
    else:
      global GLOBAL_IMPORTS_ADDED
      if self.module.module_path in GLOBAL_IMPORTS_ADDED:
        logger.debug("Already added imports in %s" % self.module.module_path)
        return
      self.insert_generic(import_code, location=Merger.BEFORE,
                          ins_module=True, ins_import=True)
      GLOBAL_IMPORTS_ADDED.add(self.module.module_path)
      return self


  def insert_enter_code(self, python_code, import_code=None):
    """
      Insert generic code at the beginning of the module. The code is wrapped
      in a ``if __name__ == '__main__'`` statement.

      :param python_code: The python code to compile and inject.
      :param import_code: The import statements, if any, to add before the
                          insertion of `python_code`. Defaults to None.
    """
    return self.insert_enter_exit_code(python_code,
                                       import_code,
                                       location=Merger.MODULE_ENTER)


  def insert_exit_code(self, python_code, import_code=None):
    """
      Insert generic code at the end of the module. The code is wrapped
      in a ``if __name__ == '__main__'`` statement.

      :param python_code: The python code to compile and inject.
      :param import_code: The import statements, if any, to add before the
                          insertion of `python_code`. Defaults to None.
    """
    return self.insert_enter_exit_code(python_code,
                                       import_code,
                                       location=Merger.MODULE_EXIT)


  def insert_enter_exit_code(self, python_code, import_code=None, location=Merger.MODULE_EXIT):
    indented_python_code = SimpleRewriter.indent(python_code, indent_level=1)
    if import_code:
      indented_import_code = SimpleRewriter.indent(import_code, indent_level=1)
      indented_python_code = indented_import_code + '\n' + indented_python_code

    new_code = EXIT_ENTER_CODE_TEMPLATE % indented_python_code
    return self.insert_generic(new_code, location)


  def inspect_all_globals(self):
    if not self.module:
      return
    co_module = self.module.code_object
    bc_module = BytecodeObject.get_parsed_code(co_module)

    for bc_tpl in bc_module:
      if bc_tpl[2] == LOAD_GLOBAL:
        self.import_lives.add(bc_tpl[3])


  @staticmethod
  def indent(original_code, indent_level=0):
    """
      Lousy helper that indents the supplied python code, so that it will fit under
      an if statement.
    """
    new_code = []
    indent = ' ' * 4 * indent_level
    for l in original_code.split('\n'):
      new_code.append(indent + l)
    return '\n'.join(new_code)


  @staticmethod
  def get_code_object(python_code):
    """
      Actually compiles the supplied code and return the ``code_object`` to be
      merged with the source ``code_object``.

      :param python_code: The python code to compile.
    """
    try:
      co = compile(python_code, '<string>', 'exec')
      return co
    except Exception, ex:
      logger.error(str(ex))
      logger.error('Compilation error:\n%s', python_code)
      return None


  # We know of some fields in KNOWN_FIELDS, and we inject them
  # using the format string
  @staticmethod
  def format_code(decl, python_code, location):
    """
      Formats the supplied ``python_code`` with format string, and values listed
      in `KNOWN_FIELDS`.

      :param decl: The declaration object (e.g., ``MethodDeclaration``, ``TypeDeclaration``, etc.).
      :param python_code: The python code to format.
      :param location: The kind of insertion to perform (e.g., ``Merger.BEFORE``).
    """
    values = SimpleRewriter.get_formatting_values(decl, location)
    return python_code.format(**values)


  @staticmethod
  def get_formatting_values(decl, location):
    """
      Retrieves the dynamic values to be added in the format string. All values
      are statically computed, but formal parameters (of methods) are passed by name so
      it is possible to dereference them in the inserted code (same for the return value).

      :param decl: The declaration object.
      :param location: The kind of insertion to perform (e.g., ``Merger.BEFORE``).
    """
    values = {}
    values['lineno'] = decl.start_lineno
    values['file_name'] = os.path.basename(decl.parent_module.module_path) \
                          if not isinstance(decl, ModuleDeclaration) \
                          else decl.module_path
    values['class_name'] = decl.parent_class.type_name \
                           if decl.parent_class is not None \
                           else None

    # Method specific arguments
    if isinstance(decl, MethodDeclaration):
      values['method_name'] = decl.method_name
      values['arguments'] = ', '.join(decl.formal_parameters) if decl.formal_parameters else None
      values['return_value'] = RETURN_CANARY_NAME if location == Merger.AFTER else None

      args = decl.formal_parameters
      length = len(args)
      for arg_cnt in range(15):
        if arg_cnt >= length:
          values['arg%d' % arg_cnt] = None
        else:
          values['arg%d' % arg_cnt] = args[arg_cnt]

    return values

