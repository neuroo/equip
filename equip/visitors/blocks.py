# -*- coding: utf-8 -*-
"""
  equip.visitors.blocks
  ~~~~~~~~~~~~~~~~~~~~~

  Callback the visit basic blocks in the program.

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""

class BlockVisitor(object):
  """
    A basic block visitor. It first receives the control-flow graph,
    and then the ``visit`` method is called with all basic blocks in
    the CFG.

    The blocks are not passed to the ``visit`` method with a particular
    order.
  """
  def __init__(self):
    self._control_flow = None

  @property
  def control_flow(self):
    return self._control_flow

  @control_flow.setter
  def control_flow(self, value):
    self._control_flow = value

  def new_control_flow(self):
    pass

  def visit(self, block):
    pass
