# -*- coding: utf-8 -*-
"""
  equip.analysis.ast.expr
  ~~~~~~~~~~~~~~~~~~~~~~~

  Minimal, high-level AST for the Python bytecode.

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""
import _ast


E_UNKNOWN = 0
E_OP = 0x1
E_LAMBDA = 0x2
E_IF = 0x4
E_DICT = 0x8
E_SET = 0x10
E_LIST_COMP = 0x20
E_SET_COMP = 0x40
E_DICT_COMP = 0x80
E_GENERATOR = 0x100
E_YIELD = 0x200
E_COMPARE = 0x400
E_CALL = 0x800
E_REPR = 0x1000
E_NUM = 0x2000
E_STR = 0x4000
E_ATTRIBUTE = 0x8000
E_SUBSCRIPT = 0x10000
E_NAME = 0x20000
E_LIST = 0x40000
E_TUPLE = 0x80000
E_BOOL_OP = 0x100000 | E_OP
E_BIN_OP = 0x200000 | E_OP
E_UNARY_OP = 0x400000 | E_OP


class Expression(object):
  def __init__(self, expr_kind=E_UNKNOWN):
    self._expr_kind = expr_kind

  @property
  def expr_kind(self):
    return self._expr_kind

  @expr_kind.setter
  def expr_kind(self, value):
    self._expr_kind = value


class Call(Expression):
  """
    Call(expr func, expr* args, keyword* keywords,
         expr? starargs, expr? kwargs)
  """
  def __init__(self, func, args=None, keywords=None, starargs=None, kwargs=None):
    Expression.__init__(self, E_CALL)
    self._func = func
    self._args = args
    self._keywords = keywords
    self._starargs = starargs
    self._kwargs = kwargs

  @property
  def func(self):
    return self._func

  @func.setter
  def func(self, value):
    self._func = value

  @property
  def args(self):
    return self._args

  @args.setter
  def args(self, value):
    self._args = value

  @property
  def keywords(self):
    return self._keywords

  @keywords.setter
  def keywords(self, value):
    self._keywords = value

  @property
  def starargs(self):
    return self._starargs

  @starargs.setter
  def starargs(self, value):
    self._starargs = value


