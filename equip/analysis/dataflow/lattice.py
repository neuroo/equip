# -*- coding: utf-8 -*-
"""
  equip.analysis.dataflow.lattice
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  The base lattice implementation (mostly used as semi-lattice).

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""


class Lattice(object):
  """
    Interface for a lattice element. Practically, we only use the semi-lattice
    with the join (V) operator.
  """
  def __init__(self):
    pass

  def init_state(self):
    """
      Returns a new initial state.
    """
    pass

  def join_all(self, *states):
    result_state = None
    for state in states:
      if result_state is None:
        result_state = state
      else:
        result_state = self.join(result_state, state)
    return result_state

  def join(self, state1, state2):
    """
      Returns the result of the V (supremum) between the two states.
    """
    pass

  def meet_all(self, *states):
    result_state = None
    for state in states:
      if result_state is None:
        result_state = state
      else:
        result_state = self.meet(result_state, state)
    return result_state

  def meet(self, state1, state2):
    """
      Returns the result of the meet \/ (infimum) between the two states.
    """
    pass


  def lte(self, state1, state2):
    """
      This is the <= operator between two lattice elements (states) as defined by:
        state1 <= state2 and state2 <= state1 <=> state1 == state2
    """
    pass


  def top(self):
    """
      The top of the lattice.
    """
    pass

  def bottom(self):
    """
      The bottom of the lattice.
    """
    pass
