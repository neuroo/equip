# -*- coding: utf-8 -*-
"""
  equip.analysis.graph.dominators
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  Dominator tree

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""

from ...utils.log import logger
from .graphs import DiGraph, Node, Edge
from .traversals import dfs_postorder_nodes

class DominatorTree(object):
  """
    Handles the dominator trees (dominator/post-dominator), and the
    computation of the dominance frontier.
  """
  def __init__(self, cfg):
    self._cfg = cfg
    self._doms = {}
    self._pdoms = {}
    self._df = {}
    self.build()

  @property
  def cfg(self):
    """
      Returns the CFG used for computing the dominator trees.
    """
    return self._cfg

  @property
  def dom(self):
    """
      Returns the dict containing the mapping of each node to its
      immediate dominator.
    """
    return self._doms

  @property
  def post_dom(self):
    """
      Returns the dict containing the mapping of each node to its
      immediate post-dominator.
    """
    return self._pdoms

  @property
  def frontier(self):
    """
      Returns the dict containing the mapping of each node to its
      dominance frontier (a set).
    """
    return self._df


  def build(self):
    try:
      graph = self.cfg.graph
      entry = self.cfg.entry_node
      exit = self.cfg.exit_node

      # Inverse the CFG to compute the post dominators using the same algo
      inverted_graph = graph.inverse()

      self.__build_dominators(graph, entry)
      self.__build_dominators(inverted_graph, exit, post_dom=True)
      self.__build_df()
    except Exception, ex:
      logger.error("Exception %s", repr(ex), exc_info=ex)


  def __build_dominators(self, graph, entry, post_dom=False):
    """
      Builds the dominator tree based on:
        http://www.cs.rice.edu/~keith/Embed/dom.pdf

      Also used to build the post-dominator tree.
    """
    doms = self._doms if not post_dom else self._pdoms
    doms[entry] = entry
    post_order = dfs_postorder_nodes(graph, entry)

    post_order_number = {}
    i = 0
    for n in post_order:
      post_order_number[n] = i
      i += 1

    def intersec(b1, b2):
      finger1 = b1
      finger2 = b2
      po_finger1 = post_order_number[finger1]
      po_finger2 = post_order_number[finger2]
      while po_finger1 != po_finger2:
        no_solution = False
        while po_finger1 < po_finger2:
          finger1 = doms.get(finger1, None)
          if finger1 is None:
            no_solution = True
            break
          po_finger1 = post_order_number[finger1]
        while po_finger2 < po_finger1:
          finger2 = doms.get(finger2, None)
          if finger2 is None:
            no_solution = True
            break
          po_finger2 = post_order_number[finger2]
        if no_solution:
          break
      return finger1

    i = 0
    changed = True
    while changed:
      i += 1
      changed = False
      for b in reversed(post_order):
        if b == entry:
          continue
        predecessors = graph.in_edges(b)
        new_idom = next(iter(predecessors)).source
        for p_edge in predecessors:
          p = p_edge.source
          if p == new_idom:
            continue
          if p in doms:
            new_idom = intersec(p, new_idom)
        if b not in doms or doms[b] != new_idom:
          doms[b] = new_idom
          changed = True
    # self.print_tree(post_dom)


  def __build_df(self):
    """
      Builds the dominance frontier.
    """
    graph = self.cfg.graph
    entry = self.cfg.entry_node

    self._df = {}
    for b in graph.nodes:
      self._df[b] = set()

    for b in graph.nodes:
      predecessors = graph.in_edges(b)
      if len(predecessors) >= 2:
        for p_edge in predecessors:
          p = p_edge.source
          runner = p
          while runner != self._doms[b]:
            self._df[runner].add(b)
            runner = self._doms[runner]


  def print_tree(self, post_dom=False):
    g_nodes = {}
    doms = self._doms if not post_dom else self._pdoms
    g = DiGraph()

    for node in doms:
      if node not in g_nodes:
        cur_node = g.make_add_node(data=node.data)
        g_nodes[node] = cur_node
      cur_node = g_nodes[node]

      parent = doms.get(node, None)
      if parent is not None and parent != node:
        if parent not in g_nodes:
          parent_node = g.make_add_node(data=parent.data)
          g_nodes[parent] = parent_node
        parent_node = g_nodes[parent]
        g.make_add_edge(parent_node, cur_node)

    logger.debug("%sDOM-tree :=\n%s", 'POST-' if post_dom else '', g.to_dot())



