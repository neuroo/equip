# -*- coding: utf-8 -*-
"""
  equip.analysis.flow
  ~~~~~~~~~~~~~~~~~~~

  Extract the control flow graphs from the bytecode.

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""
import opcode
from operator import itemgetter, attrgetter
from itertools import tee, izip
from ..utils.log import logger
from ..utils.structures import intervalmap
from ..bytecode.utils import show_bytecode

from .graph import DiGraph, Edge, Node, Walker, EdgeVisitor, Tree, TreeNode
from .graph import DominatorTree, ControlDependence
from .block import BasicBlock
from .ast import Statement, Expression
from .constraint import Constraint
from .python.effects import get_stack_effect
from .python.opcodes import *


class ControlFlow(object):
  """
    Performs the control-flow analysis on a ``Declaration`` object. It iterates
    over its bytecode and builds the basic block. The final representation
    leverages the ``DiGraph`` structure, and contains an instance of the
    ``DominatorTree``.
  """
  E_TRUE = 'TRUE'
  E_FALSE = 'FALSE'
  E_UNCOND = 'UNCOND'
  E_COND = 'COND'
  E_EXCEPT = 'EXCEPT'
  E_FINALLY = 'FINALLY'
  E_RETURN = 'RETURN'
  E_RAISE = 'RAISE'
  E_END_LOOP = 'END_LOOP'

  N_ENTRY = 'ENTRY'
  N_IMPLICIT_RETURN = 'IMPLICIT_RETURN'
  N_UNKNOWN = 'UNKNOWN'
  N_LOOP = 'LOOP'
  N_IF = 'IF'
  N_EXCEPT = 'EXCEPT'
  N_CONDITION = 'CONDITION'

  CFG_TMP_RETURN = -1
  CFG_TMP_BREAK = -2
  CFG_TMP_RAISE = -3
  CFG_TMP_CONTINUE = -4

  def __init__(self, decl):
    self._decl = decl
    self._blocks = None
    self._block_idx_map = {}
    self._block_nodes = {}
    self._block_intervals = None
    self._conds = None
    self._frames = None
    self._graph = None
    self._entry = None
    self._exit = None
    self._entry_node = None
    self._exit_node = None
    self._dom = None
    self._cdg = None
    self.analyze()

  @property
  def decl(self):
    return self._decl

  @decl.setter
  def decl(self, value):
    self._decl = value

  @property
  def entry(self):
    return self._entry

  @entry.setter
  def entry(self, value):
    self._entry = value

  @property
  def entry_node(self):
    return self._entry_node

  @entry_node.setter
  def entry_node(self, value):
    self._entry_node = value

  @property
  def exit(self):
    return self._exit

  @exit.setter
  def exit(self, value):
    self._exit = value

  @property
  def exit_node(self):
    return self._exit_node

  @exit_node.setter
  def exit_node(self, value):
    self._exit_node = value

  @property
  def blocks(self):
    """
      Returns the basic blocks created during the control flow analysis.
    """
    return self._blocks

  @property
  def block_indices_dict(self):
    """
      Returns the mapping of a bytecode indices and a basic blocks.
    """
    return self._block_idx_map

  @property
  def block_nodes_dict(self):
    """
      Returns the mapping of a basic bocks and CFG nodes.
    """
    return self._block_nodes

  @property
  def blocks_intervals(self):
    if self._block_intervals is None:
      self._block_intervals = intervalmap()
      for block in self.blocks:
        self._block_intervals[block.index:block.index + block.length] = block
    return self._block_intervals

  @property
  def block_constraints(self):
    """
      Returns the constraints associated with each ``N_CONDITION`` node
      in the CFG. This is lazily computed.
    """
    if self._conds is None:
      self.compute_conditions()
    return self._conds

  @property
  def frames(self):
    return self._frames

  @property
  def graph(self):
    """
      Returns the underlying graph that holds the CFG.
    """
    return self._graph

  @property
  def dominators(self):
    """
      Returns the ``DominatorTree`` that contains:
       - Dominator/Post-dominator tree (dict of IDom/PIDom)
       - Dominance/Post-domimance frontier (dict of CFG node -> set CFG nodes)
      This is lazily computed.
    """
    if self._dom is None:
      self._dom = DominatorTree(self)
    return self._dom

  @property
  def control_dependence(self):
    """
      Returns the ``ControlDependence`` graph. This is lazily computed.
    """
    if self._cdg is None:
      self._cdg = ControlDependence(self)
    return self._cdg

  def analyze(self):
    """
      Performs the CFA and stores the resulting CFG.
    """
    bytecode = self.decl.bytecode
    self.entry = BasicBlock(BasicBlock.ENTRY, self.decl, -1)
    self.exit = BasicBlock(BasicBlock.IMPLICIT_RETURN, self.decl, -1)

    self._blocks = ControlFlow.make_blocks(self.decl, bytecode)
    self.__build_flowgraph(bytecode)
    # logger.debug("CFG(%s) :=\n%s", self.decl, self.graph.to_dot())

  def __build_flowgraph(self, bytecode):
    g = DiGraph(multiple_edges=False)
    self.entry_node = g.make_add_node(kind=ControlFlow.N_ENTRY, data=self._entry)
    self.exit_node = g.make_add_node(kind=ControlFlow.N_IMPLICIT_RETURN, data=self._exit)

    self._block_idx_map = {}
    self._block_nodes = {}

    # Connect entry/implicit return blocks
    last_block_index, last_block = -1, None
    for block in self.blocks:
      self._block_idx_map[block.index] = block
      node_kind = ControlFlow.get_kind_from_block(block)
      block_node = g.make_add_node(kind=node_kind, data=block)
      self._block_nodes[block] = block_node
      if block.index == 0:
        g.make_add_edge(self.entry_node, self._block_nodes[block], kind=ControlFlow.E_UNCOND)
      if block.index >= last_block_index:
        last_block = block
        last_block_index = block.index
    g.make_add_edge(self._block_nodes[last_block], self.exit_node, kind=ControlFlow.E_UNCOND)

    sorted_blocks = sorted(self.blocks, key=attrgetter('_index'))
    i, length = 0, len(sorted_blocks)
    while i < length:
      cur_block = sorted_blocks[i]
      if cur_block.jumps:
        # Connect the current block to its jump targets
        for (jump_index, branch_kind) in cur_block.jumps:
          if jump_index <= ControlFlow.CFG_TMP_RETURN:
            continue
          target_block = self._block_idx_map[jump_index]
          g.make_add_edge(
            self._block_nodes[cur_block], self._block_nodes[target_block], kind=branch_kind)
      i += 1

    self._graph = g
    self.__finalize()
    self._graph.freeze()

    logger.debug("CFG :=\n%s", self._graph.to_dot())

  def __finalize(self):
    def has_true_false_branches(list_edges):
      has_true, has_false = False, False
      for edge in list_edges:
        if edge.kind == ControlFlow.E_TRUE: has_true = True
        elif edge.kind == ControlFlow.E_FALSE: has_false = True
      return has_true and has_false

    def get_cfg_tmp_values(node):
      values = set()
      for (jump_index, branch_kind) in node.data.jumps:
        if jump_index <= ControlFlow.CFG_TMP_RETURN:
          values.add(jump_index)
      return values

    def get_parent_loop(node):
      class BwdEdges(EdgeVisitor):
        def __init__(self):
          EdgeVisitor.__init__(self)
          self.edges = []

        def visit(self, edge):
          self.edges.append(edge)

      visitor = BwdEdges()
      walker = Walker(self.graph, visitor, backwards=True)
      walker.traverse(node)
      parents = visitor.edges

      node_bc_index = node.data.index
      for parent_edge in parents:
        parent = parent_edge.source
        if parent.kind != ControlFlow.N_LOOP:
          continue
        # Find the loop in which the break/current node is nested in
        if parent.data.index < node_bc_index and parent.data.end_target > node_bc_index:
          return parent
      return None

    # Burn N_CONDITION nodes
    for node in self.graph.nodes:
      out_edges = self.graph.out_edges(node)
      if len(out_edges) < 2 or not has_true_false_branches(out_edges):
        continue
      node.kind = ControlFlow.N_CONDITION

    # Handle continue/return/break statements:
    #  - blocks with continue are simply connected to the parent loop
    #  - blocks with returns are simply connected to the IMPLICIT_RETURN
    #    and previous out edges removed
    #  - blocks with breaks are connected to the end of the current loop
    #    and previous out edges removed
    for node in self.graph.nodes:
      cfg_tmp_values = get_cfg_tmp_values(node)
      if not cfg_tmp_values:
        continue
      if ControlFlow.CFG_TMP_BREAK in cfg_tmp_values:
        parent_loop = get_parent_loop(node)
        if not parent_loop:
          logger.error("Cannot find parent loop for %s", node)
          continue
        target_block = self._block_idx_map[parent_loop.data.end_target]

        out_edges = self.graph.out_edges(node)
        for edge in out_edges:
          self.graph.remove_edge(edge)

        self.graph.make_add_edge(
          node, self.block_nodes_dict[target_block], kind=ControlFlow.E_UNCOND)

      if ControlFlow.CFG_TMP_RETURN in cfg_tmp_values:
        # Remove existing out edges and add a RETURN edge to the IMPLICIT_RETURN
        out_edges = self.graph.out_edges(node)
        for edge in out_edges:
          self.graph.remove_edge(edge)
        self.graph.make_add_edge(node, self._exit_node, kind=ControlFlow.E_RETURN)

      if ControlFlow.CFG_TMP_CONTINUE in cfg_tmp_values:
        parent_loop = get_parent_loop(node)
        if not parent_loop:
          logger.error("Cannot find parent loop for %s", node)
          continue

        out_edges = self.graph.out_edges(node)
        for edge in out_edges:
          self.graph.remove_edge(edge)

        self.graph.make_add_edge(node, parent_loop, kind=ControlFlow.E_UNCOND)

    # Handle optimizations that left unreachable JUMPS
    for node in self.graph.roots():
      if node.kind == ControlFlow.N_ENTRY:
        continue
      index, lineno, op, arg, cflow_in, code_object = node.data.bytecode[0]
      if op in JUMP_OPCODES:
        self.graph.remove_node(node)

  def compute_conditions(self):
    """
      Force the computation of condition constraints on the entire CFG.
    """
    self._conds = {}
    for node in self.graph.nodes:
      if node.kind != ControlFlow.N_CONDITION:
        continue
      self.__record_condition(node)

  # Parses the conditions and convert them into symbolic conditions for
  # using in path-sensitive analysis. This essentially builds a simple
  # AST for the conditional only.
  def __record_condition(self, node):
    block = node.data
    bytecode = node.data.bytecode
    length = len(bytecode)
    if bytecode[length - 1][2] in NO_FALL_THROUGH:
      return
    i = length - 2
    cond_stack_size = 1 # Current operator takes one from the stack
    condition_bytecode = []
    k = i
    while cond_stack_size != 0:
      condition_bytecode.insert(0, bytecode[k])
      try:
        pop, push = get_stack_effect(bytecode[k][2], bytecode[k][3])
      except:
        # Skip entirely the creation of conditionals
        return
      cond_stack_size += (pop - push)
      k -= 1

    if not condition_bytecode:
      return

    def process_children(parent, j):
      if j < 0:
        return j - 1, None
      index, lineno, op, arg, cflow_in, code_object = condition_bytecode[j]
      pop, push = get_stack_effect(op, arg)

      current_node = TreeNode(kind=opcode.opname[op], data=(op, arg))
      if pop < 1:
        return j - 1, current_node

      current_node.reserve_children(pop)
      prev_offset = new_offset = j - 1
      while pop > 0:
        offset, child = process_children(current_node, new_offset)
        if child is None:
          break
        current_node.insert_child(pop - 1, child)
        prev_offset = new_offset
        new_offset = offset
        pop -= 1

      return new_offset, current_node

    cstr = Constraint()

    i = len(condition_bytecode) - 1
    _, root = process_children(None, i)
    cstr.root = root
    # Associate the out-constraint with the block
    self._conds[block] = cstr

  BLOCK_NODE_KIND = {
    BasicBlock.UNKNOWN: N_UNKNOWN,
    BasicBlock.ENTRY: N_ENTRY,
    BasicBlock.IMPLICIT_RETURN: N_IMPLICIT_RETURN,
    BasicBlock.LOOP: N_LOOP,
    BasicBlock.IF: N_IF,
    BasicBlock.EXCEPT: N_EXCEPT,
  }

  @staticmethod
  def get_kind_from_block(block):
    return ControlFlow.BLOCK_NODE_KIND[block.kind]

  @staticmethod
  def get_pairs(iterable):
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)

  @staticmethod
  def make_blocks(decl, bytecode):
    """
      Returns the set of ``BasicBlock`` that are encountered in the current bytecode.
      Each block is annotated with its qualified jump targets (if any).

      :param decl: The current declaration object.
      :param bytecode: The bytecode associated with the declaration object.
    """
    blocks = set()
    block_map = {} # bytecode index -> block
    logger.debug("CFG:\n%s", show_bytecode(bytecode))

    i, length = 0, len(bytecode)
    start_index = [j for j in range(length) if bytecode[j][0] == 0][0]
    prev_co = bytecode[start_index][5]
    prev_op = None

    slice_bytecode = [tpl for tpl in bytecode[start_index:] if tpl[5] == prev_co]

    slice_length = len(slice_bytecode)
    known_targets = ControlFlow.find_targets(slice_bytecode)
    known_targets.add(0)
    known_targets.add(1 + max([tpl[0] for tpl in slice_bytecode]))
    known_targets = list(known_targets)
    known_targets.sort()

    slice_bytecode_indexed = {}
    idx = 0
    for l in slice_bytecode:
      index = l[0]
      slice_bytecode_indexed[index] = (l, idx)
      idx += 1

    for start_index, end_index in ControlFlow.get_pairs(known_targets):
      index, lineno, op, arg, cflow_in, code_object = slice_bytecode_indexed[start_index][0]
      block_kind = ControlFlow.block_kind_from_op(op)
      cur_block = BasicBlock(block_kind, decl, start_index)
      cur_block.length = end_index - start_index - 1

      i = slice_bytecode_indexed[start_index][1]
      try:
        length = slice_bytecode_indexed[end_index][1]
        if length >= slice_length:
          length = slice_length
      except:
        length = slice_length

      while i < length:
        index, lineno, op, arg, cflow_in, code_object = slice_bytecode[i]
        if op in JUMP_OPCODES:
          jump_address = arg
          if op in opcode.hasjrel:
            jump_address = arg + index + 3

          if op in (SETUP_FINALLY, SETUP_EXCEPT, SETUP_WITH):
            kind = ControlFlow.E_UNCOND
            if op == SETUP_FINALLY: kind = ControlFlow.E_FINALLY
            if op in (SETUP_EXCEPT, SETUP_WITH): kind = ControlFlow.E_EXCEPT
            cur_block.end_target = jump_address
            cur_block.add_jump(jump_address, kind)

          elif op in (JUMP_ABSOLUTE, JUMP_FORWARD):
            cur_block.add_jump(jump_address, ControlFlow.E_UNCOND)

          elif op in (POP_JUMP_IF_FALSE, JUMP_IF_FALSE_OR_POP, FOR_ITER):
            cur_block.add_jump(jump_address, ControlFlow.E_FALSE)

          elif op in (POP_JUMP_IF_TRUE, JUMP_IF_TRUE_OR_POP):
            cur_block.add_jump(jump_address, ControlFlow.E_TRUE)

          elif op == SETUP_LOOP:
            cur_block.kind = BasicBlock.LOOP
            cur_block.end_target = jump_address

        elif op == RETURN_VALUE:
          cur_block.has_return_path = True
          cur_block.add_jump(ControlFlow.CFG_TMP_RETURN, ControlFlow.E_RETURN)

        elif op == BREAK_LOOP:
          cur_block.has_return_path = True
          cur_block.add_jump(ControlFlow.CFG_TMP_BREAK, ControlFlow.E_UNCOND)

        elif op == CONTINUE_LOOP:
          cur_block.has_return_path = False
          cur_block.add_jump(ControlFlow.CFG_TMP_CONTINUE, ControlFlow.E_UNCOND)

        elif op == RAISE_VARARGS:
          cur_block.has_return_path = False
          cur_block.add_jump(ControlFlow.CFG_TMP_RAISE, ControlFlow.E_UNCOND)

        prev_op = op
        i += 1

      # If the last block is not a NO_FALL_THROUGH, we connect the fall through
      if not cur_block.has_return_path and op not in NO_FALL_THROUGH and i < slice_length:
        kind = ControlFlow.E_UNCOND
        if op in (POP_JUMP_IF_FALSE, JUMP_IF_FALSE_OR_POP, FOR_ITER):
          kind = ControlFlow.E_TRUE
        if op in (POP_JUMP_IF_TRUE, JUMP_IF_TRUE_OR_POP):
          kind = ControlFlow.E_FALSE

        cur_block.fallthrough = True
        fallthrough_address = slice_bytecode[i][0]
        cur_block.add_jump(fallthrough_address, kind)
      else:
        cur_block.fallthrough = False

      block_map[start_index] = cur_block
      blocks.add(cur_block)

    logger.debug("Blocks := %s", blocks)

    return blocks

  @staticmethod
  def create_statements(block, bytecode, container):
    """
      Creates a set of statements out of the basic block.

      :param block: The parent basic block.
      :param bytecode: The bytecode of the basic block.
      :param container: The list that will contain all the statements in this basic block.
    """
    i = len(bytecode) - 1
    while i >= 0:
      stack_effect = 0
      j = i
      is_first = True
      while j >= 0:
        try:
          pop, push = get_stack_effect(bytecode[j][2], bytecode[j][3])
          stack_effect += (pop - push) if not is_first else pop
          is_first = False
          if stack_effect == 0:
            stmt = Statement(block, j, i)
            container.insert(0, stmt)
            break
          j -= 1
        except Exception, ex:
          stmt = Statement(block, i, i)
          container.insert(0, stmt)
          break
      i = j
      i -= 1

  @staticmethod
  def block_kind_from_op(op):
    if op in (FOR_ITER,):
      return BasicBlock.LOOP
    # Cannot make the decision at this point, need to await the finalization
    # of the CFG
    return BasicBlock.UNKNOWN

  @staticmethod
  def find_targets(bytecode):
    targets = set()
    i, length = 0, len(bytecode)
    while i < length:
      index, lineno, op, arg, cflow_in, code_object = bytecode[i]
      if op in JUMP_OPCODES:
        jump_address = arg
        if op in opcode.hasjrel:
          jump_address = arg + index + 3
        targets.add(jump_address)

        if op not in NO_FALL_THROUGH:
          targets.add(bytecode[i + 1][0])
      i += 1
    return targets

  def __repr__(self):
    return 'ControlFlow(decl=%s, blocks=%d)' % (self.decl, len(self.blocks))
