# -*- coding: utf-8 -*-
"""
  equip.analysis.graph.traversals
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  DFS/BFS and some other utils

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""

from ...utils.log import logger
from .graphs import Edge


class EdgeVisitor(object):
  def __init__(self):
    pass

  def visit(self, edge):
    pass


class Walker(object):
  """
    Traverses edges in the graph in DFS.
  """
  def __init__(self, graph, visitor, backwards=False):
    self._graph = graph
    self._visitor = visitor
    self._backwards = backwards
    self.worklist = None

  @property
  def graph(self):
    return self._graph

  @graph.setter
  def graph(self, value):
    self._graph = value

  @property
  def visitor(self):
    return self._visitor

  @visitor.setter
  def visitor(self, value):
    self._visitor = value

  def traverse(self, root):
    self.worklist = []
    self.__run(root)

  def __run(self, root=None):
    visited = set()
    if root is not None:
      self.__process(root)
    while self.worklist:
      current = self.worklist.pop(0)
      if current in visited:
        continue
      self.__process(current)
      visited.add(current)

  def __process(self, current):
    cur_node = None
    if isinstance(current, Edge):
      cur_node = current.dest if not self._backwards else current.source
      self.visitor.visit(current)
    else:
      cur_node = current

    list_edges = self.graph.out_edges(cur_node)     \
                 if not self._backwards             \
                 else self.graph.in_edges(cur_node)
    for edge in list_edges:
      self.worklist.insert(0, edge)


# Recursive version of the post-order DFS, should only be used
# when computing dominators on smallish CFGs
def dfs_postorder_nodes(graph, root):
  import sys
  sys.setrecursionlimit(5000)
  visited = set()

  def _dfs(node, _visited):
    _visited.add(node)
    for edge in graph.out_edges(node):
      dest_node = edge.dest
      if dest_node not in _visited:
        for child in _dfs(dest_node, _visited):
          yield child
    yield node

  return [n for n in _dfs(root, visited)]




