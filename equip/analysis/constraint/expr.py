# -*- coding: utf-8 -*-
"""
  equip.analysis.constraint.expr
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  Implementation of code constraints into our own AST.

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""
import opcode

from ..ast.expr import Expression

class Expr(Expression):
  """
    The ``Expr`` object with helpers for sub-classes. It also derives
    from ``ast.expr.Expression``.
  """
  UNKNOWN = 1
  CONSTANT = 2
  REFERENCE = 3
  OPERATOR = 4
  COMPARATOR = 5
  UNDEFINED = 6

  CAST_TYPE_BOOLEAN = 1
  CAST_TYPE_INTEGER = 2
  CAST_TYPE_NUMBER = 3
  CAST_TYPE_STRING = 4
  CAST_TYPE_UNKNOWN = 5

  def __init__(self, kind=UNKNOWN, data=None, terminal=False, binary=False):
    Expression.__init__(self)
    self._kind = kind
    self._data = data
    self._ast = None
    self._terminal = terminal
    self._binary = binary
    self._cast_type = Expr.CAST_TYPE_UNKNOWN

  @property
  def kind(self):
    return self._kind

  @kind.setter
  def kind(self, value):
    self._kind = value

  @property
  def data(self):
    return self._data

  @data.setter
  def data(self, value):
    self._data = value

  @property
  def ast(self):
    return self._ast

  @ast.setter
  def ast(self, value):
    self._ast = value

  @property
  def cast_type(self):
    return self._cast_type

  @cast_type.setter
  def cast_type(self, value):
    self._cast_type = value

  @property
  def terminal(self):
    return self._terminal

  @terminal.setter
  def terminal(self, value):
    self._terminal = value

  @property
  def binary(self):
    return self._binary

  @binary.setter
  def binary(self, value):
    self._binary = value

  def __ne__(self, obj):
    return True

  def __eq__(self, obj):
    return False

  def __repr__(self):
    return 'Expr(kind=%s, data=%s)' % (self.kind, repr(self.data))


class Const(Expr):
  """
    Constant expression with best-effort strong typing.
  """
  def __init__(self, data=None):
    Expr.__init__(self, Expr.CONSTANT, data, terminal=True, binary=False)
    self._is_none = False
    self._is_boolean = False
    self._is_integer = False
    self._is_string = False
    self._is_container = False
    self._is_symbol = False

  @property
  def is_none(self):
    return self._is_none

  @is_none.setter
  def is_none(self, value):
    self._is_none = value

  @property
  def is_boolean(self):
    return self._is_boolean

  @is_boolean.setter
  def is_boolean(self, value):
    self._is_boolean = value

  @property
  def boolean_value(self):
    if self.is_boolean:
      return self.data == 'True'
    return None

  @property
  def is_integer(self):
    return self._is_integer

  @is_integer.setter
  def is_integer(self, value):
    self._is_integer = value

  @property
  def integer_value(self):
    if self.is_integer:
      return int(self.data)
    return None

  @property
  def is_string(self):
    return self._is_string

  @is_string.setter
  def is_string(self, value):
    self._is_string = value

  @property
  def string_value(self):
    if self.is_string:
      return self.data
    return None

  @property
  def is_container(self):
    return self._is_container

  @is_container.setter
  def is_container(self, value):
    self._is_container = value

  def container_value(self):
    if self.is_container:
      return self.data
    return None

  @property
  def is_symbol(self):
    return self._is_symbol

  @is_symbol.setter
  def is_symbol(self, value):
    self._is_symbol = value

  @staticmethod
  def fromValue(arg, is_symbol=False):
    c = Const(data=arg)
    if arg is None:
      c.is_none = True
    elif isinstance(arg, basestring):
      c.is_string = True
    elif isinstance(arg, bool):
      c.is_boolean = True
    elif isinstance(arg, int) or isinstance(arg, long):
      c.is_integer = True
    elif isinstance(arg, tuple):
      c.is_container = True

    if is_symbol:
      c.is_symbol = True
    return c

  def __ne__(self, obj):
    return not self == obj

  def __eq__(self, obj):
    return isinstance(obj, Const) and self.data == obj.data

  def __repr__(self):
    if self.is_symbol:
      return 'Symbol(%s)' % repr(self.data)
    return 'Const(%s)' % repr(self.data)


class Ref(Expr):
  """
    Reference to a variable, function call, etc.
  """
  def __init__(self, data=None):
    Expr.__init__(self, Expr.REFERENCE, data, terminal=True, binary=False)
    self._is_var = False
    self._is_function_call = False

  @property
  def is_var(self):
    return self._is_var

  @is_var.setter
  def is_var(self, value):
    self._is_var = value

  @property
  def is_function_call(self):
    return self._is_function_call

  @is_function_call.setter
  def is_function_call(self, value):
    self._is_function_call = value

  @staticmethod
  def fromName(arg):
    return Ref(data=arg)

  def __ne__(self, obj):
    return not self == obj

  def __eq__(self, obj):
    return isinstance(obj, Ref) and self.data == obj.data

  def __repr__(self):
    return 'Ref(%s)' % self.data


BINARY_TYPE_CAST_BOOL = 1001
BINARY_TYPE_CAST_INT = 1002
BINARY_TYPE_CAST_FLOAT = 1003
BINARY_TYPE_CAST_CHAR = 1004
BINARY_TYPE_CAST_STRING = 1005
BINARY_TYPE_CAST_TUPLE = 1006

OP_MAP = {
  opcode.opmap['UNARY_POSITIVE']: {'binary': False, 'commutative': False, 'char': '+' },
  opcode.opmap['UNARY_NEGATIVE']: {'binary': False, 'commutative': False, 'char': '-' },
  opcode.opmap['UNARY_NOT']: {'binary': False, 'commutative': False, 'char': 'not' },
  opcode.opmap['UNARY_CONVERT']: {'binary': False, 'commutative': False, 'char': '`__rhs__`' },
  opcode.opmap['UNARY_INVERT']: {'binary': False, 'commutative': False, 'char': '~' },
  opcode.opmap['BINARY_POWER']: {'binary': True, 'commutative': False, 'char': '**' },
  opcode.opmap['BINARY_MULTIPLY']: {'binary': True, 'commutative': True, 'char': '*' },
  opcode.opmap['BINARY_DIVIDE']: {'binary': True, 'commutative': False, 'char': '/' },
  opcode.opmap['BINARY_MODULO']: {'binary': True, 'commutative': False, 'char': '%' },
  opcode.opmap['BINARY_ADD']: {'binary': True, 'commutative': True, 'char': '+' },
  opcode.opmap['BINARY_SUBTRACT']: {'binary': True, 'commutative': False, 'char': '-' },
  opcode.opmap['BINARY_SUBSCR']: {'binary': True, 'commutative': False, 'char': '__lhs__[__rhs__]' },
  opcode.opmap['BINARY_FLOOR_DIVIDE']: {'binary': True, 'commutative': False, 'char': '//' },
  opcode.opmap['BINARY_TRUE_DIVIDE']: {'binary': True, 'commutative': False, 'char': '/' },
  opcode.opmap['BINARY_LSHIFT']: {'binary': True, 'commutative': False, 'char': '<<' },
  opcode.opmap['BINARY_RSHIFT']: {'binary': True, 'commutative': False, 'char': '>>' },
  opcode.opmap['BINARY_AND']: {'binary': True, 'commutative': True, 'char': '&' },
  opcode.opmap['BINARY_XOR']: {'binary': True, 'commutative': True, 'char': '^' },
  opcode.opmap['BINARY_OR']: {'binary': True, 'commutative': True, 'char': '|' },
  BINARY_TYPE_CAST_BOOL: {'binary': False, 'commutative': False, 'char': 'bool(__rhs__)' },
  BINARY_TYPE_CAST_INT: {'binary': False, 'commutative': False, 'char': 'int(__rhs__)' },
  BINARY_TYPE_CAST_FLOAT: {'binary': False, 'commutative': False, 'char': 'float(__rhs__)' },
  BINARY_TYPE_CAST_CHAR: {'binary': False, 'commutative': False, 'char': 'chr(__rhs__)' },
  BINARY_TYPE_CAST_STRING : {'binary': False, 'commutative': False, 'char': 'str(__rhs__)' },
  BINARY_TYPE_CAST_TUPLE : {'binary': False, 'commutative': False, 'char': 'tuple(__rhs__)' },
}

class Operator(Expr):
  """
    An operator for the current expression (e.g., PLUS, SUBSTRACT, etc.). The
    comparison operator is commutativity-sensitive, but not w.r.t. distributivity.
  """
  def __init__(self, data=None, binary=None, commutative=None, char=None, \
               lhs=None, rhs=None):
    Expr.__init__(self, Expr.OPERATOR, data, terminal=False, binary=binary)
    self._commutative = commutative
    self._char = char
    self._lhs = None
    self._rhs = None

  @property
  def rhs(self):
    return self._rhs

  @rhs.setter
  def rhs(self, value):
    self._rhs = value

  @property
  def lhs(self):
    return self._lhs

  @lhs.setter
  def lhs(self, value):
    self._lhs = value

  @property
  def commutative(self):
    return self._commutative

  @commutative.setter
  def commutative(self, value):
    self._commutative = value

  @staticmethod
  def fromOpcode(op, arg):
    return Operator(**OP_MAP[op])

  @staticmethod
  def fromTypeMethod(method_name):
    if method_name == 'int':
      return Operator(**OP_MAP[BINARY_TYPE_CAST_INT])
    elif method_name == 'float':
      return Operator(**OP_MAP[BINARY_TYPE_CAST_FLOAT])
    elif method_name == 'bool':
      return Operator(**OP_MAP[BINARY_TYPE_CAST_BOOL])
    elif method_name == 'str':
      return Operator(**OP_MAP[BINARY_TYPE_CAST_STRING])
    elif method_name == 'chr':
      return Operator(**OP_MAP[BINARY_TYPE_CAST_CHAR])
    elif method_name == 'tuple':
      return Operator(**OP_MAP[BINARY_TYPE_CAST_TUPLE])
    return None

  def __ne__(self, obj):
    return not self == obj

  def __eq__(self, obj):
    if not isinstance(obj, Operator):
      return False
    if self._char != obj._char:
      return False
    if not self.commutative:
      return self.lhs == obj.lhs and self.rhs == obj.rhs
    else:
      return (self.lhs == obj.lhs and self.rhs == obj.rhs) \
             or (self.lhs == obj.rhs and self.rhs == obj.lhs)

  def __repr__(self):
    rr = ''
    if not self.binary:
      if '__rhs__' in self._char:
        rr = self._char.replace('__rhs__', repr(self.rhs))
      else:
        rr = self._char + repr(self.rhs)
    else:
      rr = self._char
      if '__lhs__' in rr and '__rhs__' in rr:
        for l in ('__rhs__', '__lhs__'):
          hs = self.rhs if l == '__rhs__' else self.lhs
          rr = rr.replace(l, repr(hs))
      else:
        rr = repr(self.lhs) + ' ' + self._char + ' ' + repr(self.rhs)
    return "(%s)" % rr


CMP_LESS_THAN = 1
CMP_LESS_THAN_EQUAL = 2
CMP_EQUAL = 3
CMP_NOT_EQUAL = 4
CMP_GREATER_THAN = 5
CMP_GREATER_THAN_EQUAL = 6
CMP_IN = 7
CMP_NOT_IN = 8
CMP_IS = 9
CMP_IS_NOT = 10
CMP_EX_MATCH = 11
CMP_IMPLICIT_NOT_EMPTY = 12
CMP_TYPE_CHECK = 13

CMP_MAP = {
  '<': { 'cmp_id': CMP_LESS_THAN, 'commutative': False },
  '<=' : { 'cmp_id': CMP_LESS_THAN_EQUAL, 'commutative': False },
  '==': { 'cmp_id': CMP_EQUAL, 'commutative': True },
  '!=' : { 'cmp_id': CMP_NOT_EQUAL, 'commutative': True },
  '>': { 'cmp_id': CMP_GREATER_THAN, 'commutative': False },
  '>=' : { 'cmp_id': CMP_GREATER_THAN_EQUAL, 'commutative': False },
  'in': { 'cmp_id': CMP_IN, 'commutative': False },
  'not in' : { 'cmp_id': CMP_NOT_IN, 'commutative': False },
  'is': { 'cmp_id': CMP_IS, 'commutative': True },
  'is not' : { 'cmp_id': CMP_IS_NOT, 'commutative': True },
  'exception match': { 'cmp_id': CMP_EX_MATCH, 'commutative': False },
  'not empty': { 'cmp_id': CMP_IMPLICIT_NOT_EMPTY, 'commutative': False, 'binary': False },
  'typeof': { 'cmp_id': CMP_TYPE_CHECK, 'commutative': False },
}

CMP_REPR = dict(zip([CMP_MAP[v]['cmp_id'] for v in CMP_MAP], CMP_MAP.keys()))

class Comparator(Expr):
  """
    A comparator operator for expressions.
  """
  def __init__(self, data=None, cmp_id=None, commutative=False, binary=True):
    Expr.__init__(self, Expr.COMPARATOR, data, terminal=False, binary=binary)
    self._cmp_id = cmp_id
    self._commutative = commutative
    self._lhs = None
    self._rhs = None

  @property
  def rhs(self):
    return self._rhs

  @rhs.setter
  def rhs(self, value):
    self._rhs = value

  @property
  def lhs(self):
    return self._lhs

  @lhs.setter
  def lhs(self, value):
    self._lhs = value

  @property
  def cmp_id(self):
    return self._cmp_id

  @cmp_id.setter
  def cmp_id(self, value):
    self._cmp_id = value

  @property
  def commutative(self):
    return self._commutative

  @commutative.setter
  def commutative(self, value):
    self._commutative = value

  @staticmethod
  def fromOpcode(op, arg):
    return Comparator(**CMP_MAP[arg])

  @staticmethod
  def fromKind(kind):
    return Comparator(**CMP_MAP[CMP_REPR[kind]])

  def __ne__(self, obj):
    return not self == obj

  def __eq__(self, obj):
    if not isinstance(obj, Comparator):
      return False
    if self.cmp_id != obj.cmp_id:
      return False
    if not self.commutative:
      return self.lhs == obj.lhs and self.rhs == obj.rhs
    else:
      return (self.lhs == obj.lhs and self.rhs == obj.rhs) \
             or (self.lhs == obj.rhs and self.rhs == obj.lhs)

  def __repr__(self):
    if not self.binary:
      return '(%s %s)' % (CMP_REPR[self.cmp_id], repr(self.rhs))
    return '(%s %s %s)' % (repr(self.lhs), CMP_REPR[self.cmp_id], repr(self.rhs))


class Undef(Expr):
  def __init__(self, data=None):
    Expr.__init__(self, Expr.UNDEFINED, data, terminal=True, binary=False)

  def __ne__(self, obj):
    return True

  def __eq__(self, obj):
    return False

  def __repr__(self):
    return 'Undef'


