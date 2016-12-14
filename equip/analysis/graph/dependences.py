# -*- coding: utf-8 -*-
"""
  equip.analysis.graph.dependences
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  Control dependence graph.

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""

from ...utils.log import logger
from .graphs import DiGraph, Node, Edge


class ControlDependence(object):
  """
    Holds the control dependence. Each node in the CFG is mapped to
    its dependences.
  """
  def __init__(self, cfg):
    self._cfg = cfg
    self._dom = cfg.dominators
    self._graph = None
    self.build()

  @property
  def cfg(self):
    return self._cfg

  @property
  def graph(self):
    return self._graph

  def build(self):
    self._graph = DiGraph()

    for node in self._dom.post_dom:
      p_frontier = self._dom.post_frontier[node]
      if not p_frontier:
        continue
      self._graph.add_node(node)
      for f_node in p_frontier:
        self._graph.make_add_edge(f_node, node)

    self._graph.freeze()
