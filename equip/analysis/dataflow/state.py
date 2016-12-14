# -*- coding: utf-8 -*-
"""
  equip.analysis.dataflow.state
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  State propagated in the CFG for dataflow analysis.

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""

import copy

class Transfer(object):
  """
    Interface for the transfer function used for dataflow analysis.
  """
  def __init__(self):
    pass


  def run(self, node, input_state):
    """
      Returns a new state from the evaluation of the node w.r.t. the
      input state.

      :param node: The node being currently analyzed.
      :param input_state: The state at the beginning of the node.
    """
    pass


class State(dict):
  """
    State object to represent the current state for a given
    node of the CFG. This is just a wrapper around a ``dict`` until
    we switch to functional data structures.
  """

  def copy(self):
    return copy.deepcopy(self)

  def __repr__(self):
    return 'State<%s>(%s)' % (hex(id(self))[-5:], dict.__repr__(self))


class States(object):
  """
    Represents the environment for the dataflow analysis. It holds the
    mapping of states per node in the CFG. This is only usable when the
    dataflow analysis is path-insensitive. In path-sensitive dataflow
    analysis, the state is predicated by path constraints (the feasibility
    of the actual path that led to the dataflow state).
  """

  def __init__(self, lattice, start_node):
    self._nodes = set()
    self._store_in = {}
    self._store_out = {}
    self._store_in[start_node] = lattice.init_state()
    self._store_out[start_node] = lattice.init_state()

  @property
  def nodes(self):
    return self._nodes

  def set_input(self, node, state):
    self._nodes.add(node)
    self._store_in[node] = state

  def input(self, node):
    return self._store_in[node]

  def output(self, node):
    return self._store_out[node]

  def set_output(self, node, state):
    self._nodes.add(node)
    self._store_out[node] = state

  def __repr__(self):
    buffer = []
    for node in self._nodes:
      buffer.append('Node %s' % node)
      buffer.append('  --> IN  := ' + repr(self.input(node)))
      buffer.append('  --> OUT := ' + repr(self.output(node)))
    return '\n'.join(buffer)
