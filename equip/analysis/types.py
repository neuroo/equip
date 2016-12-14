# -*- coding: utf-8 -*-
"""
  equip.analysis.types
  ~~~~~~~~~~~~~~~~~~~~

  A simple fwd/bwd type inference.

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""
import opcode
import copy
import _ast
from operator import itemgetter
from ..utils.log import logger

from .dataflow import ForwardDataflow,  \
                      BackwardDataflow, \
                      Lattice,          \
                      State,            \
                      Transfer
from .constraint.expr import CMP_TYPE_CHECK
from .ast.utils import dump_native_ast,     \
                       split_assignment,    \
                       serialize_name_attr, \
                       named_expr_iterator, \
                       contained_expr
from .dataflow.utils import dict_union
from .python.types import *
from .python.opcodes import *

from .graph import DiGraph, Edge, Node, Walker, EdgeVisitor
from ..bytecode.utils import show_bytecode

from .defs import DefUse


def unify_types(output_state, input_state, typed_expr):
  same_exprs = contained_expr(output_state, typed_expr)
  if not same_exprs:
    # The expression, does not exist, then we just add it
    output_state[typed_expr] = input_state[typed_expr]
  elif len(same_exprs) == 1:
    output_state[typed_expr] = output_state[same_exprs[0]]
  else:
    all_same = len(set(same_exprs)) == 1
    if not all_same:
      union = UnionType()
      for expr in same_exprs:
        union.add(output_state[expr])
      output_state[typed_expr] = union


class TypeLattice(Lattice):
  def __init__(self):
    Lattice.__init__(self)

  def init_state(self):
    return State({})

  def join(self, state1, state2):
    result_state = state1.copy()
    for typed_expr in state2:
      unify_types(result_state, state2, typed_expr)
    return result_state

  def meet(self, state1, state2):
    raise Exception()



class TypeTransfer(Transfer):
  def __init__(self, defs, cfg, existing_types=None):
    Transfer.__init__(self)
    self._defs = defs
    self._cfg = cfg
    self._existing_types = existing_types

  @property
  def defs(self):
    return self._defs

  @property
  def cfg(self):
    return self._cfg

  @property
  def existing_types(self):
      return self._existing_types

  def run(self, node, input_state):
    result_state = input_state.copy()
    block = node.data

    constraints = self.cfg.block_constraints

    for stmt in block.statements:
      native = stmt.native
      if isinstance(native, _ast.Assign) or isinstance(native, _ast.AugAssign):
        self.transfer_assign(result_state, native, stmt.start_bytecode_index)

      elif isinstance(native, _ast.Expr):
        value = native.value
        logger.debug("Stmt kind: %s", type(value))
        if isinstance(value, _ast.Call):
          self.transfer_call(result_state, native, stmt.start_bytecode_index)
      else:
        logger.error("Unknown stmt: %s", dump_native_ast(native))

    return result_state


  # Assign: a <- b
  def transfer_assign(self, stmt_state, native_stmt, stmt_index):
    stores, load_expr = split_assignment(native_stmt)
    for store_expr in stores:
      stmt_state[store_expr] = self.expr_type(load_expr, stmt_state)
      logger.debug("S{0x%04x}: %s <- %s",
                   stmt_index, dump_native_ast(store_expr), stmt_state[store_expr])

  # f
  def transfer_call(self, stmt_state, native_expr, stmt_index):
    pass

  # Inspect the type of the expression
  def expr_type(self, load_expr, stmt_state):
    logger.debug("Typeof: %s", dump_native_ast(load_expr))
    if load_expr is None:
      return NoneType()
    elif is_numeric(load_expr):
      return numeric_typeof(load_expr)
    elif is_sequence(load_expr):
      return sequence_typeof(load_expr)
    elif is_dict(load_expr):
      return dict_typeof(load_expr)
    elif is_set(load_expr):
      return set_typeof(load_expr)
    else:
      same_exprs = contained_expr(stmt_state, load_expr)
      if same_exprs:
        if len(same_exprs) > 1:
          # if all types are the same, we just return this type
          all_same = len(set(same_exprs)) == 1
          if not all_same:
            union = UnionType()
            for expr in same_exprs:
              union.add(stmt_state[expr])
          else:
            return stmt_state[same_exprs[0]]
        else:
          return stmt_state[same_exprs[0]]

    logger.debug("UnknownType for load_expr: %s", dump_native_ast(load_expr))
    return UnknownType()


class TypeInference(object):
  def __init__(self, cfg):
    self._cfg = cfg
    self._defs = DefUse(self._cfg)
    self._lattice = TypeLattice()
    self._transfer = TypeTransfer(self._defs, self._cfg)
    self.build()

  @property
  def cfg(self):
    return self._cfg

  def build(self):
    fwd_analysis = ForwardDataflow(self.cfg, self._lattice, self._transfer)
    fwd_analysis.analyze()
    logger.debug("States:\n%s", fwd_analysis.states)

    # bwd_analysis = BackwardDataflow(self.cfg, self._lattice, self._transfer)
    # bwd_analysis.analyze()
    #logger.debug("States:\n%s", bwd_analysis.states)

