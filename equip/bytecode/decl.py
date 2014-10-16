# -*- coding: utf-8 -*-
"""
  equip.bytecode.decl
  ~~~~~~~~~~~~~~~~~~~

  Structured representation of Module, Types, Method, Imports.

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""
import dis
from operator import attrgetter, \
                     methodcaller

from ..utils.log import logger
from ..visitors.bytecode import BytecodeVisitor
from .utils import update_nested_code_object


class Declaration(object):
  """
    Base class for the declaration types of object.
  """
  MODULE = 1
  TYPE = 2
  METHOD = 3
  FIELD = 4
  IMPORT = 5

  def __init__(self, kind, _code_object):
    self._kind = kind
    self._code_object = _code_object
    self._parent = None
    self._children = []
    self._lines = None
    self._bytecode = []
    self._bytecode_object = None
    self._has_changes = False

  @property
  def lines(self):
    """
      A tuple of start/end line numbers that encapsulates this declaration.
    """
    return self._lines

  @lines.setter
  def lines(self, value):
      self._lines = value

  @property
  def start_lineno(self):
    """
      Returns the start line number of the declaration.
    """
    return self._lines[0] if self._lines else -1

  def get_start_lineno(self):
    return self.start_lineno

  @property
  def end_lineno(self):
    """
      Returns the end line number of the declaration.
    """
    return self._lines[1] if self._lines else -1

  @property
  def parent(self):
    """
      Returns the parent of this declaration or ``None`` if there is
      no parent (e.g., for a ``ModuleDeclaration``).
    """
    return self._parent

  @parent.setter
  def parent(self, value):
    logger.debug("Set parent. %s", value)
    self._parent = value
    self._parent.add_child(self)

  @property
  def children(self):
    """
      Returns the children of this declaration.
    """
    return self._children

  def add_child(self, child):
    """
      Adds a child to this declaration.

      :param child: A ``Declaration`` that is a child of the current declaration.
    """
    self._children.append(child)
    logger.debug("add_child:: Children: %s", self.children)
    # Keep sorting by line number
    self._children = sorted(self._children, key=methodcaller('get_start_lineno'))

  @property
  def parent_module(self):
    """
      Returns the parent module (a ``ModuleDeclaration``) for this declaration.
    """
    return self.__get_parent_kind(ModuleDeclaration)

  @property
  def parent_class(self):
    """
      Returns the parent class (a ``TypeDeclaration``) for this declaration.
    """
    return self.__get_parent_kind(TypeDeclaration)

  @property
  def parent_method(self):
    """
      Returns the parent method (a ``MethodDeclaration``) for this declaration.
    """
    return self.__get_parent_kind(MethodDeclaration)

  def __get_parent_kind(self, kind):
    p = self.parent
    while p is not None:
      if isinstance(p, kind):
        return p
      p = p.parent
    return None

  @property
  def bytecode(self):
    """
      Returns the bytecode associated with this declaration.
    """
    return self._bytecode

  @bytecode.setter
  def bytecode(self, value):
    self._bytecode = value

  @property
  def code_object(self):
    return self._code_object

  @code_object.setter
  def code_object(self, value):
    self._code_object = value

  def update_nested_code_object(self, original_co, new_co):
    self._code_object = update_nested_code_object(self._code_object,
                                                  original_co,
                                                  new_co)
    self._has_changes = True

  @property
  def has_changes(self):
    return self._has_changes

  @has_changes.setter
  def has_changes(self, value):
    self._has_changes = value

  # Mostly reserved
  @property
  def bytecode_object(self):
    return self._bytecode_object

  @bytecode_object.setter
  def bytecode_object(self, value):
      self._bytecode_object = value


  def accept(self, visitor):
    if isinstance(visitor, BytecodeVisitor):
      for i in xrange(len(self._bytecode)):
        index, lineno, op, arg, cflow_in, _ = self._bytecode[i]
        visitor.visit(index, op, arg=arg, lineno=lineno, cflow_in=cflow_in)


  is_module = lambda self: self.kind == Declaration.MODULE
  is_type = lambda self: self.kind == Declaration.TYPE
  is_method = lambda self: self.kind == Declaration.METHOD
  is_field = lambda self: self.kind == Declaration.FIELD
  is_import = lambda self: self.kind == Declaration.IMPORT

  @property
  def kind(self):
    return self._kind



class ImportDeclaration(Declaration):
  """
    Models an import statement. It handles relatives/absolute
    imports, as well as aliases.
  """

  def __init__(self, code_object):
    Declaration.__init__(self, Declaration.IMPORT, code_object)
    self._root = None
    self._aliases = None
    self._live_names = None
    self._dots = -1
    self._star = False

  @property
  def star(self):
      return self._star

  @star.setter
  def star(self, value):
      self._star = value

  @property
  def aliases(self):
    return self._aliases

  @aliases.setter
  def aliases(self, value):
    self._aliases = value

  @property
  def live_names(self):
    if self._live_names is None:
      self._live_names = set()
      for (name, alias) in self.aliases:
        if alias is None:
          if '.' not in name:
            self._live_names.add(name)
          else:
            live_name = name[:name.rfind('.')]
            self._live_names.add(live_name)
        else:
          self._live_names.add(alias)
    return self._live_names

  @property
  def dots(self):
    return self._dots

  @dots.setter
  def dots(self, value):
    self._dots = value

  @property
  def root(self):
    return self._root

  @root.setter
  def root(self, value):
    self._root = value

  def __eq__(self, obj):
    return self.root == obj.root and self.aliases == obj.aliases and self.dots == obj.dots

  def __repr__(self):
    skip_import_root = False
    import_buffer = ''
    if self.dots > 0:
      import_buffer += 'from ' + '.' * self.dots
      if self.root:
        import_buffer += self.root
        skip_import_root = True
      import_buffer += ' import '

    elif self.root:
      import_buffer += 'from '
    else:
      import_buffer += 'import '

    if self.root and not skip_import_root:
      import_buffer += self.root + ' import '

    if self.star:
      import_buffer += '*'

    import_list = []
    for aliased_name in self.aliases:
      local_import = aliased_name[0]
      if aliased_name[1]:
        local_import += ' as ' + aliased_name[1]
      import_list.append(local_import)

    if import_list:
      import_buffer += ', '.join(import_list)

    return 'Import(%s)' % import_buffer



class ModuleDeclaration(Declaration):
  """
    The module is the object that captures everything under one pyc file.
    It contains nested classes and functions, as well as import statements.
  """

  def __init__(self, module_path, code_object):
    Declaration.__init__(self, Declaration.MODULE, code_object)
    self._module_path = module_path

    self._imports = []
    self._classes = None
    self._functions = None

  def add_import(self, importDecl):
    if importDecl not in self._imports:
      self._imports.append(importDecl)

  @property
  def imports(self):
    return self._imports

  @property
  def module_path(self):
    return self._module_path

  @property
  def classes(self):
    if self._classes is None:
      self._classes = [ c for c in self.children if c.is_type() ]
    return self._classes

  @property
  def functions(self):
    if self._functions is None:
      self._functions = [ f for f in self.children if f.is_method() ]
    return self._functions

  def __repr__(self):
    return 'ModuleDeclaration(path=%s, co=%s)' % (self.module_path, self.code_object)


class TypeDeclaration(Declaration):
  """
    Represent a class declaration. It has a name, as well as a hierarchy
    (superclass). The type contains several methods and fields, and can
    have nested types.
  """

  def __init__(self, type_name, code_object):
    Declaration.__init__(self, Declaration.TYPE, code_object)
    self._type_name = type_name

    self._superclasses = []
    self._methods = None
    self._fields = None
    self._nested_types = None

  @property
  def type_name(self):
    """
      Returns the name of the type.
    """
    return self._type_name

  @property
  def superclasses(self):
    return self._superclasses

  @property
  def methods(self):
    """
      Returns a list of ``MethodDeclaration`` that belong to this type.
    """
    if self._methods is None:
      self._methods = [ f for f in self.children if f.is_method() ]
    return self._methods

  @property
  def fields(self):
    return self.fields

  @property
  def nested_types(self):
    """
      Returns a list of ``TypeDeclaration`` that belong to this type.
    """
    if self._nested_types is None:
      self._nested_types = [ c for c in self.children if c.is_type() ]
    return self._nested_types

  def __repr__(self):
    return 'TypeDeclaration#%d(name=%s)' % (self.start_lineno, self.type_name)


class MethodDeclaration(Declaration):
  """
    The declaration of a method or a function.
  """

  def __init__(self, method_name, code_object):
    Declaration.__init__(self, Declaration.METHOD, code_object)
    self._method_name = method_name

    self._formal_parameters = []
    self._body = None
    self._labels = dis.findlabels(code_object.co_code)
    self._nested_types = []

  @property
  def body(self):
    return self._body

  @body.setter
  def body(self, value):
    self._body = value

  @property
  def labels(self):
    return self._labels

  @property
  def formal_parameters(self):
    return self._formal_parameters

  @formal_parameters.setter
  def formal_parameters(self, value):
    self._formal_parameters = value

  @property
  def method_name(self):
    return self._method_name

  @property
  def nested_types(self):
    return self._nested_types

  def __repr__(self):
    return 'MethodDeclaration#%d(name=%s, args=%s)' \
           % (self.start_lineno, self.method_name, self.formal_params)


class FieldDeclaration(Declaration):
  def __init__(self, field_name, code_object):
    Declaration.__init__(self, Declaration.FIELD, code_object)
    self._field_name = field_name

  @property
  def field_name(self):
    return self._field_name
