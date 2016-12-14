# -*- coding: utf-8 -*-
"""
  equip.analysis.dataflow.fixedpoint
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  The implementations of the fixedpoint algorithm for dataflow analysis.
  Either forward/backward.

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""
from fn.immutable import SkewHeap, LinkedList
from ...utils.log import logger

from .lattice import Lattice
from .state import States


class Dataflow(object):
  """
    A lattice-based dataflow analysis framework.
  """

  MAX_STEPS = 500

  def __init__(self, cfg, lattice, transfer, path_sensitive=False, start_states=None):
    self._cfg = cfg
    self._lattice = lattice
    self._transfer = transfer
    self._states = None
    self._forward = None
    self._path_sensitive = path_sensitive
    self._start_states = start_states
    self.worklist = []

  @property
  def forward(self):
    return self._forward

  @forward.setter
  def forward(self, value):
    self._forward = value

  @property
  def path_sensitive(self):
    return self._path_sensitive

  @path_sensitive.setter
  def path_sensitive(self, value):
    self._path_sensitive = value

  @property
  def cfg(self):
    return self._cfg

  @property
  def lattice(self):
    return self._lattice

  @property
  def transfer(self):
    return self._transfer

  @property
  def states(self):
    return self._states

  def init(self):
    """
      Initializes the analysis by having the start node only in the worklist,
      and create its initial state.
    """
    start_node = self.cfg.entry_node if self.forward else self.cfg.exit_node
    self._states = States(self.lattice, start_node) # XXX: use start states

    self.worklist = []
    for node in self.cfg.graph.nodes:
      self._states.set_input(node, self.lattice.init_state())
      self._states.set_output(node, self.lattice.init_state())
      if node != self.cfg.exit_node:
        self.worklist.append(node)

  def join(self, node):
    """
      Join states for the upcoming node. In forward analysis, it gets the
      output states from predecessors in the CFG and join the states to take
      it as the input state of the current node. It does the converse in
      backward analysis (i.e., ``out_state <- join(input states of successors)``).
    """
    cur_state = None
    if self.forward:
      if node == self.cfg.entry_node:
        cur_state = self.lattice.init_state()
      else:
        edges = self.cfg.graph.in_edges(node)
        states = [self.states.output(pred_edge.source) for pred_edge in edges]
        cur_state = self.lattice.join_all(*states)

      self.states.set_input(node, cur_state)
    else:
      edges = self.cfg.graph.out_edges(node)
      if len(edges) == 1:
        succ_node = next(iter(edges)).dest
        if succ_node == self.cfg.exit_node:
          cur_state = self.lattice.init_state()
        else:
          cur_state = self.states.input(succ_node)
      else:
        states = [self.states.input(pred_edge.dest) for pred_edge in edges]
        cur_state = self.lattice.join_all(*states)

      self.states.set_output(node, cur_state)

  def flow(self, node):
    """
      Implements the flow properties between the input of a CFG node (basic block)
      and its output. It calls the transfer function to compute the flow of the block
      and compares it with the previous (or next) state to see if the dataflow converged,
      which leads to stopping the exploration.
    """
    state_in = self.states.input(node)
    state_out = self.states.output(node)

    prev_state = state_out if self.forward else state_in
    input_state = state_in if self.forward else state_out
    new_state = self.transfer.run(node, input_state)

    if self.forward:
      self.states.set_output(node, new_state)
    else:
      self.states.set_input(node, new_state)

    return new_state != prev_state


  def analyze(self):
    """
      Starts the dataflow analysis.
    """
    self.init()
    self.__internal_fixedpoint()


  def __internal_fixedpoint(self):
    if self.forward is None:
      raise Exception('Dataflow analysis direction not set')
    if self.states is None:
      raise Exception('States should be initialized')

    steps = 0
    while True:
      if steps > Dataflow.MAX_STEPS:
        raise Exception('Stopped dataflow analysis. Maximum number of steps reached.')
      steps += 1
      if not self.worklist:
        break

      node = self.worklist.pop(0)
      self.join(node)

      if not self.flow(node):
        # state convergence
        continue

      next_edges = self.cfg.graph.out_edges(node) if self.forward else self.cfg.graph.in_edges(node)
      for edge in next_edges:
        next_node = edge.dest if self.forward else edge.source
        if next_node != self.cfg.exit_node:
          self.worklist.append(next_node)

    if self.forward:
      self.join(self.cfg.exit_node)


class ForwardDataflow(Dataflow):
  def __init__(self, cfg, lattice, transfer, path_sensitive=False, start_states=None):
    Dataflow.__init__(self, cfg, lattice, transfer, path_sensitive)
    self.forward = True


class BackwardDataflow(Dataflow):
  def __init__(self, cfg, lattice, transfer, path_sensitive=False, start_states=None):
    Dataflow.__init__(self, cfg, lattice, transfer, path_sensitive)
    self.forward = False


