# -*- coding: utf-8 -*-
"""
  equip.analysis.defs
  ~~~~~~~~~~~~~~~~~~~

  A simple implementation of the DefUse dataflow algorithm.

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""
import opcode
import _ast
import copy
from operator import itemgetter
from ..utils.log import logger

from .dataflow import ForwardDataflow, \
                      Lattice,         \
                      State,           \
                      Transfer
from .dataflow.utils import dict_union
from .ast.utils import dump_native_ast,     \
                       split_assignment,    \
                       serialize_name_attr, \
                       named_expr_iterator
from .graph import DiGraph, Edge, Node, Walker, EdgeVisitor
from ..bytecode.utils import show_bytecode
from .python.opcodes import *

GEN = 0x1
USE = 0x2
KILL = 0x4
GEN_USE = (GEN, USE, KILL)


class DefLattice(Lattice):
  """
    The lattice being used for def-use analysis.
  """
  def __init__(self):
    Lattice.__init__(self)


  def init_state(self):
    return State({GEN: {}, USE: {}, KILL: {}})


  def join(self, state1, state2):
    result_state = state1.copy()
    for guk in GEN_USE:
      result_state[guk] = dict_union(state1[guk], state2[guk])
    return result_state


  def meet(self, state1, state2):
    raise Exception()


class DefTransfer(Transfer):
  """
    The transfer function for def-use analysis.
  """
  def __init__(self):
    Transfer.__init__(self)
    self.length = -1


  def run(self, node, input_state):
    result_state = input_state.copy()
    block = node.data

    for stmt in block.statements:
      native = stmt.native
      if not native:
        continue
      if isinstance(native, _ast.Assign) or isinstance(native, _ast.AugAssign):
        self.transfer_assign(result_state, native, stmt.start_bytecode_index)
      else:
        self.transfer_load(result_state, native, stmt.start_bytecode_index)

    return result_state


  @staticmethod
  def update_gen_kill(stmt_state, var, index):
    if var == 'None':
      return
    if var not in stmt_state[GEN]:
      stmt_state[GEN][var] = set()
    else:
      # Generate a kill for the previous GENs
      if var not in stmt_state[KILL]:
        stmt_state[KILL][var] = set(stmt_state[GEN][var])
      else:
        stmt_state[KILL][var] = stmt_state[KILL][var].union(stmt_state[GEN][var])
      stmt_state[GEN][var] = set()

    stmt_state[GEN][var].add(index)


  @staticmethod
  def update_use(stmt_state, var, index):
    if var not in stmt_state[USE]:
      stmt_state[USE][var] = set()
    stmt_state[USE][var].add(index)


  # Assign: a <- b
  def transfer_assign(self, stmt_state, native_stmt, stmt_index):
    stores, _ = split_assignment(native_stmt)
    for store_expr in stores:
      store_name = serialize_name_attr(store_expr)
      DefTransfer.update_gen_kill(stmt_state, store_name, stmt_index)


  # Use: Expr(a)
  def transfer_load(self, stmt_state, native_stmt, stmt_index):
    for named_expr in named_expr_iterator(native_stmt):
      load_name = serialize_name_attr(named_expr)
      DefTransfer.update_use(stmt_state, load_name, stmt_index)


class DefUse(object):
  """
    The def-use analysis. It first performs a forward dataflow analysis
    and later builds a mapping between definitions and uses of variables.
  """
  def __init__(self, cfg):
    self._cfg = cfg
    self._defs = {} # var -> { gen block -> set(use blocks) }
    self._uses = {} # var -> { use block -> gen block }
    self._escaped = set()
    self._lattice = DefLattice()
    self._transfer = DefTransfer()
    self.build()

  @property
  def definitions(self):
    """
      Returns the dictionary that contains the mapping between a variable name,
      its definition block and the uses blocks.
    """
    return self._defs

  @property
  def use_sites(self):
    """
      Returns the dictionary that contains the mapping between a variable name,
      its use blocks and for each use block the possible definition blocks.
    """
    return self._uses

  @property
  def cfg(self):
    """
      Returns the CFG used for performing this def-use analysis.
    """
    return self._cfg

  @property
  def escaped(self):
    """
      Returns the set of variables that escaped.
    """
    return self._escaped


  def build(self):
    analysis = ForwardDataflow(self.cfg, self._lattice, self._transfer)
    analysis.analyze()
    self.__build_stores(analysis.states)


  def __build_stores(self, states):
    # For each use, add an edge to its possible defs
    for node in states.nodes:
      if node == self.cfg.exit_node:
        continue
      out_state = states.output(node)
      block = node.data

      for var in out_state[USE]:
        possible_gens = out_state[GEN][var] if var in out_state[GEN] else None
        if possible_gens is None:
          self._escaped.add(var)
        else:
          # Resolve the node in the CFG that contain the GEN
          for gen_index in possible_gens:
            gen_block = self.cfg.blocks_intervals[gen_index]

            if var not in self._defs:
              self._defs[var] = {}
            if gen_block not in self._defs[var]:
              self._defs[var][gen_block] = set()
            self._defs[var][gen_block].add(block)

            if var not in self._uses:
              self._uses[var] = {}
            if block not in self._uses[var]:
              self._uses[var][block] = set()
            self._uses[var][block].add(gen_block)

