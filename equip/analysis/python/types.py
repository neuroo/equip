# -*- coding: utf-8 -*-
"""
  equip.analysis.python.types
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~

  Knowledge of Python type system and builtin types.

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""
from __future__ import absolute_import
import types
import _ast
from ..ast.utils import serialize_name_attr

BOOLEAN_TYPE = (bool,)
NUMERIC_TYPES = (int, long, float, complex)
SEQUENCE_TYPES = (str, unicode, list, tuple, bytearray, buffer, xrange, basestring)
SET_TYPES = (set, frozenset)
DICT_TYPE = (dict,)

BUILTIN_TYPES = NUMERIC_TYPES + SEQUENCE_TYPES + SET_TYPES + DICT_TYPE

ITERATOR_REQUIRED_METHODS = ('__iter__', 'next')


class GenericType(object):
  pass

class UnknownType(GenericType):
  def __init__(self):
    GenericType.__init__(self)

  def __repr__(self):
    return 'unknown'

class NumericType(GenericType):
  def __init__(self):
    GenericType.__init__(self)

  def __repr__(self):
    return 'numeric'

class NoneType(GenericType):
  def __init__(self):
    GenericType.__init__(self)

  def __repr__(self):
    return 'none'

class BooleanType(GenericType):
  def __init__(self):
    GenericType.__init__(self)

  def __repr__(self):
    return 'boolean'

class IntType(GenericType):
  def __init__(self):
    GenericType.__init__(self)

  def __repr__(self):
    return 'int'

class LongType(GenericType):
  def __init__(self):
    GenericType.__init__(self)

  def __repr__(self):
    return 'long'

class FloatType(GenericType):
  def __init__(self):
    GenericType.__init__(self)

  def __repr__(self):
    return 'float'

class ComplexType(GenericType):
  def __init__(self):
    GenericType.__init__(self)

  def __repr__(self):
    return 'complex'

class StringType(GenericType):
  def __init__(self):
    GenericType.__init__(self)

  def __repr__(self):
    return 'string'

class TupleType(GenericType):
  def __init__(self):
    GenericType.__init__(self)

  def __repr__(self):
    return 'tuple'

class ListType(GenericType):
  def __init__(self):
    GenericType.__init__(self)

  def __repr__(self):
    return 'list'

class DictType(GenericType):
  def __init__(self):
    GenericType.__init__(self)

  def __repr__(self):
    return 'dict'

class FunctionType(GenericType):
  def __init__(self):
    GenericType.__init__(self)

  def __repr__(self):
    return 'function'

class LambdaType(GenericType):
  def __init__(self):
    GenericType.__init__(self)

  def __repr__(self):
    return 'lambda'

class GeneratorType(GenericType):
  def __init__(self):
    GenericType.__init__(self)

  def __repr__(self):
    return 'generator'

class ObjectType(GenericType):
  def __init__(self):
    GenericType.__init__(self)
    self._attributes = None

  @property
  def attributes(self):
      return self._attributes

  @attributes.setter
  def attributes(self, value):
      self._attributes = value

  def __repr__(self):
    return 'object{%s}' % (', '.join(self._attributes) if self._attributes else '')

class MethodType(GenericType):
  def __init__(self):
    GenericType.__init__(self)

  def __repr__(self):
    return 'method'

class FileType(GenericType):
  def __init__(self):
    GenericType.__init__(self)

  def __repr__(self):
    return 'file'

class XRangeType(GenericType):
  def __init__(self):
    GenericType.__init__(self)

  def __repr__(self):
    return 'xrange'

class TracebackType(GenericType):
  def __init__(self):
    GenericType.__init__(self)

  def __repr__(self):
    return 'traceback'

class SequenceType(GenericType):
  def __init__(self):
    GenericType.__init__(self)

  def __repr__(self):
    return 'sequence'

class UnionType(GenericType):
  def __init__(self):
    GenericType.__init__(self)
    self._types = set()

  @property
  def types(self):
      return self._types

  def add(self, _type):
    self._types.add(_type)

  def __repr__(self):
    return 'Union{%s}' % repr(self.types)


def numeric_typeof(ast_node):
  assert type(ast_node) == _ast.Num

  value = ast_node.n
  if value is None:
    return NoneType()

  if isinstance(value, int):
    return IntType()
  elif isinstance(value, long):
    return LongType()
  elif isinstance(value, float):
    return FloatType()
  elif isinstance(value, complex):
    return ComplexType()

  return NumericType()


def is_numeric(ast_node):
  return isinstance(ast_node, _ast.Num)


def sequence_typeof(ast_node):
  if isinstance(ast_node, _ast.Str):
    return StringType()
  elif isinstance(ast_node, _ast.Tuple):
    return TupleType()
  elif isinstance(ast_node, _ast.List):
    return ListType()

  return SequenceType()


def is_sequence(ast_node):
  return isinstance(ast_node, _ast.Str)   \
      or isinstance(ast_node, _ast.Tuple) \
      or isinstance(ast_node, _ast.List)


def is_dict(ast_node):
  return isinstance(ast_node, _ast.Dict)


def dict_typeof(ast_node=None):
  return DictType()


def is_set(ast_node):
  return isinstance(ast_node, _ast.Set)


def set_typeof(ast_node=None):
  return SetType()


