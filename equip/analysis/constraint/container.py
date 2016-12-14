# -*- coding: utf-8 -*-
"""
  equip.analysis.constraint.container
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  Constraint container.

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""
import opcode
from ...utils.log import logger

from ..graph import Tree, TreeNode

from .expr import Expr, Const, Ref, Comparator, Operator, Undef, \
                  CMP_IMPLICIT_NOT_EMPTY, CMP_TYPE_CHECK, OP_MAP, CMP_MAP
from ..python.opcodes import *


class Constraint(object):
  """
    Represents a constraint in the bytecode. This is used to represent
    conditional expressions. We store both the bytecode AST constraint
    and a final internal representation (can be used to compare constraints
    or generate SMT clauses).
  """
  def __init__(self):
    self._ast = Tree()
    self._cstr = None
    self._live = None
    self._root = None

  @property
  def root(self):
    return self._root

  @root.setter
  def root(self, value):
    self._root = value
    self._ast.root = self._root

  @property
  def ast(self):
    return self._ast

  @property
  def live(self):
    if self._live is None:
      self._live = set()
      worklist = [self.tree]
      while worklist:
        cur = worklist.pop(0)
        if isinstance(cur, Ref):
          self._live.add(cur.data)
        else:
          if not cur.terminal:
            worklist.append(cur.rhs)
            if cur.binary:
              worklist.append(cur.lhs)

    return self._live

  @property
  def tree(self):
    if self._cstr is None:
      self.__finalize()
    return self._cstr

  def has_comparator(self, cmp_kind):
    worklist = [self.tree]
    while worklist:
      cur = worklist.pop(0)
      logger.debug("Cur := %s", cur)
      if isinstance(cur, Comparator):
        if cur.cmp_id == cmp_kind:
          return True
        worklist.append(cur.lhs)
        if cur.rhs is not None:
          worklist.append(cur.rhs)
      elif isinstance(cur, Operator):
        worklist.append(cur.lhs)
        if cur.rhs is not None:
          worklist.append(cur.rhs)
    return False

  def __ne__(self, obj):
    return not self == obj

  def __eq__(self, obj):
    return isinstance(obj, Constraint) and self.tree == obj.tree


  def __finalize(self):
    root = self.root
    self._cstr = None
    if root.data[0] != COMPARE_OP:
      self._cstr = Comparator.fromKind(CMP_IMPLICIT_NOT_EMPTY)
    else:
      self._cstr = Comparator.fromOpcode(*root.data)
    self._cstr.data = root.data

    def process_children(cstr_node, ast_node):
      if ast_node.has_children() and cstr_node.terminal:
        return

      if not cstr_node.terminal:
        if cstr_node.kind == Expr.COMPARATOR and cstr_node.cmp_id in (CMP_IMPLICIT_NOT_EMPTY, CMP_TYPE_CHECK):
          if cstr_node.cmp_id == CMP_IMPLICIT_NOT_EMPTY:
            cstr_node.rhs = convert_ast_constraint(ast_node)
            process_children(cstr_node.rhs, ast_node)
          else:
            lhs_child = ast_node.first_child
            cstr_node.lhs = convert_ast_constraint(lhs_child)
            process_children(cstr_node.lhs, lhs_child)

            if ast_node.num_children() > 1:
              rhs_child = ast_node.child(1)
              cstr_node.rhs = convert_ast_constraint(rhs_child)
              process_children(cstr_node.rhs, rhs_child)
        else:
          expected_children_num = 2 if cstr_node.binary else 1
          children = ast_node.children
          num_children = len([c for c in children if c is not None])
          if num_children != expected_children_num:
            logger.debug("Consistency error. expected %d, got %d children for %s",
                         expected_children_num, num_children, ast_node)
            cstr_node.rhs = Undef(data=None)
            if expected_children_num == 2:
              cstr_node.lhs = Undef(data=None)
          elif expected_children_num == 1:
            child = ast_node.first_child
            cstr_node.rhs = convert_ast_constraint(child)
            process_children(cstr_node.rhs, child)
          else:
            lhs_child = ast_node.first_child
            rhs_child = ast_node.last_child

            cstr_node.lhs = convert_ast_constraint(lhs_child)
            process_children(cstr_node.lhs, lhs_child)

            cstr_node.rhs = convert_ast_constraint(rhs_child)
            process_children(cstr_node.rhs, rhs_child)

    logger.debug("Current tree := %s", self._ast.to_dot())

    process_children(self._cstr, root)


  def __repr__(self):
    return repr(self._cstr)


def convert_ast_constraint(ast_node):
  """
    Returns a new ``Expr`` node.

    :param ast_node: The current AST node in the conditional.
  """
  op, arg = ast_node.data

  if op in OP_MAP:
    # We got an operator
    return Operator.fromOpcode(op, arg)
  elif op == COMPARE_OP and arg in CMP_MAP:
    return Comparator.fromOpcode(op, arg)
  elif op in LOAD_OPCODES:
    if op == LOAD_CONST:
      return Const.fromValue(arg)
    else:
      if arg in ('True', 'False', 'None', 'str', 'int', 'bool', 'chr', 'float', 'tuple'):
        return Const.fromValue(arg, is_symbol=True)
      return Ref.fromName(arg)
  elif op in CALL_OPCODES:
    if is_type_check(ast_node):
      return Comparator.fromKind(CMP_TYPE_CHECK)
    elif is_type_cast(ast_node):
      return Operator.fromTypeMethod(ast_call_node.first_child.data[1])
    else:
      return Undef(data=ast_node.data)
  else:
    logger.debug("Not converted node: op=%s, arg=%s", opcode.opname[op], repr(arg))

  return Undef(data=ast_node.data)


def is_type_check(ast_call_node):
  method_name = ast_call_node.first_child.data[1]
  return method_name in ('isinstance', 'type')

def is_type_cast(ast_call_node):
  method_name = ast_call_node.first_child.data[1]
  return method_name in ('str', 'int', 'bool', 'chr', 'float', 'tuple')


