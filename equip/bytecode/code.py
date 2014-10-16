# -*- coding: utf-8 -*-
"""
  equip.bytecode.code
  ~~~~~~~~~~~~~~~~~~~

  Parsing and representation of the supplied bytecode.

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""
import dis
import opcode
import marshal
import time
import struct
import types
import operator
import traceback
import imp
from dis import findlinestarts, findlabels

from ..utils.log import logger

from .utils import show_bytecode
from .decl import ModuleDeclaration, \
                  TypeDeclaration,   \
                  MethodDeclaration, \
                  FieldDeclaration,  \
                  ImportDeclaration

from ..visitors.bytecode import BytecodeVisitor
from ..visitors.classes import ClassVisitor
from ..visitors.methods import MethodVisitor
from ..visitors.modules import ModuleVisitor


# Flags from code.h
CO_OPTIMIZED              = 0x0001      # use LOAD/STORE_FAST instead of _NAME
CO_NEWLOCALS              = 0x0002      # only cleared for module/exec code
CO_VARARGS                = 0x0004
CO_VARKEYWORDS            = 0x0008
CO_NESTED                 = 0x0010      # ???
CO_GENERATOR              = 0x0020
CO_NOFREE                 = 0x0040      # set if no free or cell vars
CO_GENERATOR_ALLOWED      = 0x1000      # unused
# The future flags are only used on code generation, so we can ignore them.
# (It does cause some warnings, though.)
CO_FUTURE_DIVISION        = 0x2000
CO_FUTURE_ABSOLUTE_IMPORT = 0x4000
CO_FUTURE_WITH_STATEMENT  = 0x8000


POP_TOP = 1
IMPORT_STAR = 84
BUILD_CLASS = 89
STORE_NAME = 90
LOAD_CONST = 100
LOAD_ATTR = 106
IMPORT_NAME = 108
IMPORT_FROM = 109
STORE_FAST = 125
MAKE_FUNCTION = 132


class BytecodeObject(object):
  """
    This class parses the bytecode from a file and constructs the representation from it.
    The result is:

    * One module (type: ``ModuleDeclaration``)
    * The bytecode expanded into intelligible structure.
    * Construction of nested declarations, and hierarchy of declaration types.
  """

  def __init__(self, pyc_file, lazy_load=True):
    """
      Builds the representation of the bytecode, as well as the nested ``Declaration``
      structures based on the bytecode contained in the binary file.

      :param pyc_file: The compiled python file that contains the bytecode.
    """
    self.code = None
    self.magic = None
    self.moddate = None
    self.modif_date = None
    self.pyc_file = pyc_file
    if not lazy_load:
      self.parse()
    self.main_module = None
    self.bytecode = []
    self.all_decls = set()


  def parse(self):
    """
      Parses the binary file (pyc) and extract the bytecode out of it. Keeps the magic number
      as well as the timestamp for serialization.
    """
    fd = open(self.pyc_file, 'rb')
    self.magic = fd.read(4)
    self.moddate = fd.read(4)
    self.modif_date = long(struct.unpack('<l', self.moddate)[0])
    self.code = marshal.load(fd)
    self.bytecode = []

    try:
      self.load_bytecode(self.code)
      self.build_representation()
    except Exception, ex:
      logger.error("parse error: %s", repr(ex), exc_info=ex)


  def get_module(self):
    """
      Returns the ModuleDeclaration associated with the current bytecode.
    """
    return self.main_module


  def get_bytecode(self):
    """
      Returns the current translated bytecode.
    """
    return self.bytecode


  @property
  def declarations(self):
    """
      Returns a set of all the declarations found in the current bytecode.
    """
    return self.all_decls


  @property
  def has_changes(self):
    """
      Returns `True` if any change was performed on the module. This is used
      to know if we need to rewrite or not a pyc file.
    """
    return self.main_module.has_changes


  def accept(self, visitor):
    """
      Runs the visitor over the nested declarations found in the this module, or
      the entire bytecode if it's a `BytecodeVisitor`.
    """
    if not self.code:
      self.parse()

    if isinstance(visitor, BytecodeVisitor):
      for i in xrange(len(self.bytecode)):
        index, lineno, op, arg, cflow_in, _ = self.bytecode[i]
        visitor.visit(index, op, arg=arg, lineno=lineno, cflow_in=cflow_in)

    elif isinstance(visitor, ModuleVisitor):
      visitor.visit(self.main_module)

    elif isinstance(visitor, ClassVisitor) or isinstance(visitor, MethodVisitor):
      if not self.main_module:
        logger.debug("No main_module")
        return
      self.__depth_visitor_run(visitor)


  def __depth_visitor_run(self, visitor):
    """
      Needs to traverse the entire tree structure of declaration objects, to execute
      the visitor over them.
    """
    logger.debug("Execute visitor on: %s, main_module=%s", visitor, self.main_module)

    cache = set()
    is_class_visitor = isinstance(visitor, ClassVisitor)
    stack = [self.main_module]
    while stack:
      current = stack.pop()
      children = current.children
      logger.debug("Visit children: %s", children)
      for child in children:
        if not child:
          continue
        if (is_class_visitor and isinstance(child, TypeDeclaration))      \
        or (not is_class_visitor and isinstance(child, MethodDeclaration)):
          if child in cache:
            continue
          visitor.visit(child)
          cache.add(child)
        stack.insert(0, child)


  def add_enter_code(self, python_code, import_code=None):
    """
      Adds enter callback in the module. The callback code (both ``import_code`` and
      ``python_code``) is wrapped in a main test if statement::

        if __name__ == '__main__':
          import_code
          python_code

      :param python_code: Python code to inject before the module gets executed (if it's executed
                          under main). The code is not executed if it's not under main.
      :param import_code: Python code that contains the import statements that might be required
                          by the injected ``python_code``. Defaults to None.
    """
    from ..rewriter.simple import SimpleRewriter

    rewriter = SimpleRewriter(self.main_module)
    rewriter.insert_enter_code(python_code, import_code)


  def add_exit_code(self, python_code, import_code=None):
    """
      Adds exit callback in the module. The callback code (both ``import_code`` and
      ``python_code``) is wrapped in a main test if statement::

        if __name__ == '__main__':
          import_code
          python_code

      :param python_code: Python code to inject after the module gets executed (if it's executed
                          under main). The code is not executed if it's not under main.
      :param import_code: Python code that contains the import statements that might be required
                          by the injected ``python_code``. Defaults to None.
    """
    from ..rewriter.simple import SimpleRewriter

    rewriter = SimpleRewriter(self.main_module)
    rewriter.insert_exit_code(python_code, import_code)


  def write(self):
    """
      Persists the changes in the bytecode. This overwrites the current file that
      contains the bytecode with the new bytecode while preserving the timestamp.

      Note that the magic number if changed to be the one from the current Python
      version that runs the instrumentation process.
    """
    if not self.has_changes:
      logger.debug("Skip writing %s, no changes detected.", self.main_module.module_path)
      return

    try:
      new_co = self.main_module.code_object

      # Always keep the changed time from the source
      source_file = self.main_module.module_path.replace('.pyc', '.py')
      timestamp = self.modif_date
      try:
        timestamp = long(os.stat(source_file).st_mtime)
      except:
        pass
      fd = open(self.main_module.module_path, 'wb')
      fd.write('\0\0\0\0') # Magic placeholder
      fd.write(struct.pack('<l', timestamp))
      marshal.dump(new_co, fd)
      fd.flush()
      fd.seek(0, 0)
      fd.write(imp.get_magic())
      fd.close()
      logger.debug("Wrote file %s", self.main_module.module_path)
      return True
    except Exception, ex:
      logger.error("Exception- %s", str(ex))
      logger.error("\n%s", traceback.format_exc())
      return False


  def build_representation(self):
    """
      Builds the internal representation of declarations and how they relate to
      each other. It works by creating a map of type/method declaration indices,
      and then associate the bytecode for each of them.

      When all declarations are created, the parenting process runs and creates
      the tree structure of the decalrations, such as::

         ModuleDeclaration()
           - TypeDeclaration(name='SomeClass')
              - MethodDeclaration#lineno(name='methodOfSomeClass')
              - MethodDeclaration#lineno(name='otherMethodOfSomeClass')

      This representation is required to run the visitors.
    """
    if not self.bytecode:
      return

    decl_counter = 0
    self.all_decls = set()
    decl_map = {}

    class_decl_indices, method_decl_indices = BytecodeObject.find_classes_methods(self.bytecode)
    interest_indices = class_decl_indices.union(method_decl_indices)

    current_co = self.bytecode[0][5]
    self.main_module = ModuleDeclaration(self.pyc_file, current_co)
    self.main_module.bytecode = self.bytecode
    self.main_module.bytecode_object = self

    module_lines = (1, max([self.bytecode[i][1] for i in xrange(len(self.bytecode))]), decl_counter)
    self.main_module.lines = module_lines
    BytecodeObject.parse_imports(self.main_module, self.bytecode)
    decl_map[module_lines] = self.main_module
    decl_counter += 1

    for tpl_indices in interest_indices:
      decl = None
      start_index, end_index = tpl_indices
      index, lineno, op, arg, _, co = self.bytecode[start_index]
      end_lineno = max([self.bytecode[i][1] for i in xrange(start_index, min(end_index + 1, len(self.bytecode)))])
      decl_co = BytecodeObject.next_code_object(self.bytecode, start_index)

      lines_tuple = (lineno, end_lineno, decl_counter)

      i = start_index
      if tpl_indices in class_decl_indices:
        # Class specific information
        decl = TypeDeclaration(decl_co.co_name, decl_co)
      else:
        # Method specific information
        decl = MethodDeclaration(decl_co.co_name, decl_co)
        decl.formal_params = BytecodeObject.get_formal_params(decl_co)

      decl.bytecode = self.bytecode[start_index:end_index]
      decl.lines = lines_tuple[:2]

      self.all_decls.add(decl)
      decl_map[lines_tuple] = decl
      decl_counter += 1

    # Process parenting
    decl_map_items = decl_map.keys()
    decl_map_items = sorted(decl_map_items, key=operator.itemgetter(2), reverse=True)
    for lines_tuple in decl_map_items:
      candidates = list()
      for ltpl in decl_map:
        if (ltpl[0] < lines_tuple[0] or lines_tuple[0] == 1 == ltpl[0]) \
        and ltpl[1] >= lines_tuple[1] \
        and ltpl[2] != lines_tuple[2]:
          candidates.append(ltpl)

      if candidates:
        # Minimize the differences
        candidates = sorted(candidates, cmp=lambda t1, t2: (t1[1] - t1[0]) - (t2[1] - t2[0]))
        best_candidate = candidates[0]

        child_elmt = decl_map[lines_tuple]
        parent_elmt = decl_map[best_candidate]
        # Check that we don't have a recursive parent/child (e.g. a module with just one function)
        if parent_elmt.parent == child_elmt or child_elmt.parent == parent_elmt:
          continue
        child_elmt.parent = parent_elmt
        logger.debug("Parent %s <- Child %s", parent_elmt, child_elmt)

    logger.debug(BytecodeObject.build_tree(self.main_module))


  @staticmethod
  def build_tree(root, indent=''):
    """
      Returns a string that represents the tree of ``Declaration`` types.
    """
    buffer = ''
    buffer += indent + repr(root) + '\n'
    for c in root.children:
      buffer += BytecodeObject.build_tree(c, indent + '    ')
    return buffer


  @staticmethod
  def finalize_decl_object(kind, acc_data):
    pass


  @staticmethod
  def next_code_object(bytecode, index):
    i = index
    while i < len(bytecode):
      co = bytecode[i][3]
      if isinstance(co, types.CodeType):
        return co
      i += 1
    return None


  @staticmethod
  def prev_code_object(bytecode, index):
    i = index
    while i <= 0:
      co = bytecode[i][3]
      if isinstance(co, types.CodeType):
        return co
      i -= 1
    return None


  @staticmethod
  def find_classes_methods(bytecode):
    """
      Finds the indices of the clases and methods declared in the bytecode. This is done
      by matching line numbers of the declaration and the ``MAKE_FUNCTION`` or ``BUILD_CLASS``
      opcode.
    """
    class_indices = set()
    method_indices = set()
    class_lines = set()
    method_lines = set()

    for tpl in bytecode:
      lineno, op_code = tpl[1], tpl[2]
      if op_code == BUILD_CLASS:
        class_lines.add(lineno)
      elif op_code == MAKE_FUNCTION:
        method_lines.add(lineno)

    method_lines = method_lines.difference(class_lines)

    def unroll_through_end(s_lineno, j, length, start_index):
      j += 1
      while j < length and bytecode[j][1] == s_lineno:
        j += 1
      if j >= length - 1:
        return j - 1

      while j < length:
        tpl = bytecode[j]
        index, lineno, op_code = tpl[0], tpl[1], tpl[2]
        if lineno == s_lineno:
          while j < length and bytecode[j][1] == s_lineno:
            j += 1
          return j - 1
        j += 1
      return j


    # Once we get the line numbers, we need to go and find the indices
    # for the start/end of the declarations
    blacklist = set()
    i, length = 0, len(bytecode)
    while i < length:
      tpl = bytecode[i]
      index, lineno, op_code = tpl[0], tpl[1], tpl[2]
      if lineno in blacklist:
        i += 1
        continue

      if lineno in class_lines:
        start_index = i
        end_index = unroll_through_end(lineno, i, length, start_index)
        class_indices.add(( start_index, end_index ))
        blacklist.add(lineno)

      elif lineno in method_lines:
        start_index = i
        end_index = unroll_through_end(lineno, i, length, start_index)
        method_indices.add(( start_index, end_index ))
        blacklist.add(lineno)

      i += 1

    return class_indices, method_indices


  @staticmethod
  def get_formal_params(code_object):
    """
      Returns the ordered list of formal parameters (arguments) of a method.

      :param code_object: The code object of the method.
    """
    varargs = bool(code_object.co_flags & CO_VARARGS)
    varkwargs = bool(code_object.co_flags & CO_VARKEYWORDS)
    args = code_object.co_varnames[:code_object.co_argcount + varargs + varkwargs]
    return args


  def load_bytecode(self, code_object):
    BytecodeObject.parse_code_object(code_object, self.bytecode)
    # logger.debug("Bytecode for %s:\n%s" % (code_object, show_bytecode(self.bytecode)))


  @staticmethod
  def get_parsed_code(code_object):
    bytecode = []
    BytecodeObject.parse_code_object(code_object, bytecode)
    return bytecode


  @staticmethod
  def parse_code_object(code_object, bytecode):
    """
      Parses the bytecode (``co_code`` field of the code object) and dereferences the
      ``oparg`` for later analysis.

      :param code_object: The code object containing the bytecode to analyze
      :param bytecode: The list that will be used to append the expanded bytecode
                       sequences.
    """
    if not code_object:
      return
    code = code_object.co_code

    labels = findlabels(code_object.co_code)
    linestarts = dict(findlinestarts(code_object))

    global_free = code_object.co_cellvars + code_object.co_freevars
    newlocals = bool(code_object.co_flags & CO_NEWLOCALS)

    length = len(code)
    i = 0
    lineno = -1
    extended_arg = 0

    while i < length:
      c = code[i]
      op = ord(c)

      if i in linestarts:
        lineno = linestarts[i]

      arg1 = None
      cflow_in = i in labels
      current_index = i
      i += 1

      if op >= opcode.HAVE_ARGUMENT:
        oparg = ord(code[i]) + (ord(code[i+1]) << 8) + extended_arg
        i += 2
        label = -1
        extended_arg = 0

        if op == opcode.EXTENDED_ARG:
          extended_arg = (oparg << 16)

        if op in opcode.hasconst:
          arg1 = code_object.co_consts[oparg]
        elif op in opcode.hasname:
          arg1 = code_object.co_names[oparg]
        elif op in opcode.haslocal:
          arg1 = code_object.co_varnames[oparg]
        elif op in opcode.hascompare:
          arg1 = opcode.cmp_op[oparg]
        elif op in opcode.hasfree:
          arg1 = global_free[oparg]
        elif op in opcode.hasjrel:
          arg1 = oparg
        elif op in opcode.hasjabs:
          arg1 = oparg
        else:
          arg1 = oparg

      bytecode.append((current_index, lineno, op, arg1, cflow_in, code_object))

      if arg1 and isinstance(arg1, types.CodeType):
        BytecodeObject.parse_code_object(arg1, bytecode)


  @staticmethod
  def parse_imports(main_module, bytecode):
    """
      Extracts and adds import statements to the ``ModuleDeclaration``.
    """
    import_stmts = BytecodeObject.get_imports_from_bytecode(main_module.code_object,
                                                            bytecode)
    for imp_stmt in import_stmts:
      main_module.add_import(imp_stmt)


  @staticmethod
  def get_imports_from_bytecode(code_object, bytecode):
    """
      Parses the import statements from the bytecode and constructs a list of
      ``ImportDeclaration``.
    """
    last_import_ref_idx = BytecodeObject.get_last_import_ref(bytecode,
                                                             code_object)
    imports_bc = bytecode[:last_import_ref_idx + 1]

    import_stmts = []
    final_import_stmts = []

    # Split all the imports into single statements
    started = False
    buffer = []
    for tpl in imports_bc:
      if tpl[2] == LOAD_CONST and isinstance(tpl[3], int):
        started = True
        if len(buffer) > 0:
          import_stmts.append(buffer)
        buffer = []
      if started:
        buffer.append(tpl)
    if len(buffer) > 0:
      import_stmts.append(buffer)

    logger.debug("Found %d import statements", len(import_stmts))
    for import_stmt in import_stmts:
      arg = import_stmt[0][3]

      import_star = False
      import_root = None
      aliased_names = [] # [(import_name, import_alias)]
      num_dots = arg if arg >= 0 else 0 # We have -1 if it's not a relative import

      i, length = 0, len(import_stmt)
      while i < length:
        op, arg = import_stmt[i][2], import_stmt[i][3]
        next_op = import_stmt[i + 1][2] if i < length - 1 else -1
        next_next_op = import_stmt[i + 2][2] if i < length - 2 else -1

        if op in (IMPORT_NAME, IMPORT_FROM) and next_op in (STORE_NAME, STORE_FAST):
          # Simple import statement
            next_arg = import_stmt[i + 1][3]
            if next_arg == arg or arg.startswith(next_arg + '.'):
              # No alias
              aliased_names.append((arg, None))
            else:
              aliased_names.append((arg, next_arg))
        elif op == IMPORT_NAME and next_op == LOAD_ATTR and next_next_op == STORE_NAME:
          next_arg = import_stmt[i + 2][3]
          aliased_names.append((arg, next_arg))
        elif op == IMPORT_NAME:
          if import_root is not None:
            logger.error("Already defined a root: %s vs current %s", import_root, arg)
          if arg:
            import_root = arg

          if next_op == IMPORT_STAR:
            import_star = True
        i += 1

      # Instantiate the import stmt in the module
      imp_stmt = ImportDeclaration(code_object)
      imp_stmt.root = import_root
      imp_stmt.star = import_star
      imp_stmt.dots = num_dots
      imp_stmt.aliases = aliased_names
      final_import_stmts.append(imp_stmt)

    return final_import_stmts


  # Fine the last reference to an import stmt in the current code_object
  @staticmethod
  def get_last_import_ref(bytecode, code_object):
    """
      Find the last reference of an import statement in the bytecode.
    """
    i, length = 0, len(bytecode)
    last_index = -1
    while i < length:
      op, co = bytecode[i][2], bytecode[i][5]
      if op in (IMPORT_FROM, IMPORT_NAME) and co == code_object:
        last_index = i
      i += 1

    if last_index > -1:
      # Need to unroll until the next STORE_NAME
      while last_index < length:
        op = bytecode[last_index][2]
        if op == STORE_NAME:
          break
        last_index += 1
    return last_index

