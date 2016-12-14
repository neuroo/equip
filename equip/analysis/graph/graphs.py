# -*- coding: utf-8 -*-
"""
  equip.analysis.graph.graphs
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~

  Graph data structures

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""
import copy
from ...utils.log import logger


class Node(object):
  GLOBAL_COUNTER = 0

  def __init__(self, kind=None, data=None):
    Node.GLOBAL_COUNTER += 1
    self._id = Node.GLOBAL_COUNTER
    self._kind = kind
    self._data = data

  @property
  def gid(self):
    return self._id

  @property
  def kind(self):
    return self._kind

  @kind.setter
  def kind(self, value):
    self._kind = value

  @property
  def data(self):
    return self._data

  @data.setter
  def data(self, value):
    self._data = value

  def __ne__(self, obj):
    return not self == obj

  def __eq__(self, obj):
    return isinstance(obj, Node) and obj.gid == self.gid

  def __hash__(self):
    return hash('node-' + str(self.gid))

  def __repr__(self):
    return 'Node%d(kind=%s, data=%s)' % (self.gid, repr(self.kind), repr(self.data))


class Edge(object):
  GLOBAL_COUNTER = 0

  def __init__(self, source=None, dest=None, kind=None, data=None):
    Edge.GLOBAL_COUNTER += 1
    self._id = Edge.GLOBAL_COUNTER
    self._source = source
    self._dest = dest
    self._kind = kind
    self._data = data
    self._inversed = False
    self._weight = 1

  @property
  def gid(self):
    return self._id

  @property
  def source(self):
    return self._source

  @source.setter
  def source(self, value):
    self._source = value

  @property
  def dest(self):
    return self._dest

  @dest.setter
  def dest(self, value):
    self._dest = value

  @property
  def kind(self):
    return self._kind

  @kind.setter
  def kind(self, value):
    self._kind = value

  @property
  def data(self):
    return self._data

  @data.setter
  def data(self, value):
    self._data = value

  @property
  def weight(self):
    return self._weight

  @weight.setter
  def weight(self, value):
    self._weight = value

  @property
  def inversed(self):
    return self._inversed

  def inverse(self):
    tmp = self._source
    self._source = self._dest
    self._dest = tmp
    self._inversed = True

  def __ne__(self, obj):
    return not self == obj

  def __eq__(self, obj):
    return isinstance(obj, Edge) and obj.gid == self.gid

  def __hash__(self):
    return hash('edge-' + str(self.gid))

  def __repr__(self):
    return 'Edge%d(src=%s, dst=%s, kind=%s, data=%s)' \
           % (self.gid, self.source, self.dest, repr(self.kind), repr(self.data))


class DiGraph(object):
  """
    A simple directed-graph structure.
  """

  def __init__(self, multiple_edges=True):
    self._multiple_edges = multiple_edges
    self._nodes = set()
    self._edges = set()
    self._in = {} # dest -> source : set(edges)
    self._out = {} # source -> dest : set(edges)
    self._immutable = False
    self._imm_in = None # src -> set(in edges)
    self._imm_out = None # src -> set(out edges)

  @property
  def multiple_edges(self):
    return self._multiple_edges

  @multiple_edges.setter
  def multiple_edges(self, value):
    self._multiple_edges = value

  @property
  def immutable(self):
    return self._immutable

  @immutable.setter
  def immutable(self, value):
    self._immutable = value

  @property
  def nodes(self):
    return self._nodes

  @property
  def edges(self):
    return self._edges

  def add_edge(self, edge):
    if self.immutable:
      raise Exception('The graph is now immutable. Cannot add edge.')
    if edge in self._edges:
      raise Exception('Edge already present')
    source_node, dest_node = edge.source, edge.dest

    if not self.multiple_edges:
      # If we already connected src and dest, return
      if source_node in self._out and dest_node in self._out[source_node]:
        logger.error("Already connected nodes: %s", edge)
        return
      if dest_node in self._in and source_node in self._in[dest_node]:
        logger.error("Already connected nodes: %s", edge)
        return

    self._edges.add(edge)
    self.add_node(source_node)
    self.add_node(dest_node)
    DiGraph.__add_edge(self._out, source_node, dest_node, edge)
    DiGraph.__add_edge(self._in, dest_node, source_node, edge)

  def remove_edge(self, edge):
    if self.immutable:
      raise Exception('The graph is now immutable. Cannot remove edge.')
    if edge not in self.edges:
      return
    source_node, dest_node = edge.source, edge.dest
    DiGraph.__remove_edge(self._out, source_node, dest_node, edge)
    DiGraph.__remove_edge(self._in, dest_node, source_node, edge)
    self._edges.remove(edge)

  @staticmethod
  def __add_edge(in_out, source, dest, edge):
    if source not in in_out:
      in_out[source] = {}
    if dest not in in_out[source]:
      in_out[source][dest] = list()
    in_out[source][dest].append(edge)

  @staticmethod
  def __remove_edge(in_out, source, dest, edge):
    if source not in in_out:
      return
    if dest not in in_out[source]:
      return
    if edge in in_out[source][dest]:
      in_out[source][dest].remove(edge)
    if not in_out[source][dest]:
      in_out[source].pop(dest, None)
    if not in_out[source]:
      in_out.pop(source, None)

  def has_node(self, node):
    return node in self.nodes

  def add_node(self, node):
    if self.immutable:
      raise Exception('The graph is now immutable. Cannot add node.')
    self._nodes.add(node)

  def remove_node(self, node):
    if self.immutable:
      raise Exception('The graph is now immutable. Cannot remove node.')
    if node not in self._nodes:
      return
    # Remove all edges that touched this node
    self._edges = set([e for e in self._edges if e.source != node and e.dest != node])
    # Clean up _in/_out
    for src in self._in:
      self._in[src].pop(node, None)
    for dest in self._out:
      self._out[dest].pop(node, None)
    if node in self._in:
      self._in.pop(node, None)
    if node in self._out:
      self._out.pop(node, None)
    # Finally remove the node
    self._nodes.remove(node)

  def in_edges(self, node):
    if self.immutable:
      return self._imm_in[node]
    else:
      if not self.has_node(node) or node not in self._in:
        return list()
      return list([e for n in self._in[node] for e in self._in[node][n]])

  def out_edges(self, node):
    if self.immutable:
      return self._imm_out[node]
    else:
      if not self.has_node(node) or node not in self._out:
        return list()
      return list([e for n in self._out[node] for e in self._out[node][n]])

  def in_degree(self, node):
    return len(self.in_edges(node))

  def out_degree(self, node):
    return len(self.out_edges(node))

  def to_dot(self):
    from .io import DotConverter
    return DotConverter.process(self)

  def roots(self):
    r = set()
    for n in self.nodes:
      if self.in_degree(n) < 1:
        r.add(n)
    return r

  def freeze(self):
    if self.immutable:
      return

    self._imm_in = {}
    self._imm_out = {}
    for node in self.nodes:
      self._imm_in[node] = self.in_edges(node)
      self._imm_out[node] = self.out_edges(node)

    self._in = None
    self._out = None
    self.immutable = True

  def unfreeze(self):
    if not self.immutable:
      return
    self._in = {}
    self._out = {}

    for edge in self.edges:
      source_node, dest_node = edge.source, edge.dest
      DiGraph.__add_edge(self._out, source_node, dest_node, edge)
      DiGraph.__add_edge(self._in, dest_node, source_node, edge)

    self._imm_in = None
    self._imm_out = None
    self.immutable = False

  def copy(self):
    return copy.deepcopy(self)

  # Some helpers
  def make_add_node(self, kind=None, data=None):
    if self.immutable:
      raise Exception('The graph is now immutable. Cannot add node.')
    node = DiGraph.make_node(kind=kind, data=data)
    self.add_node(node)
    return node

  def make_add_edge(self, source=None, dest=None, kind=None, data=None):
    if self.immutable:
      raise Exception('The graph is now immutable. Cannot add edge.')
    edge = DiGraph.make_edge(source=source, dest=dest, kind=kind, data=data)
    self.add_edge(edge)
    return edge

  def inverse(self):
    """
      Returns a frozen copy of this graph where all edges have been inverted.
    """
    new_g = DiGraph(multiple_edges=self.multiple_edges)
    for edge in self.edges:
      new_edge = copy.deepcopy(edge)
      new_edge.inverse()
      new_g.add_edge(new_edge)
    new_g.freeze()
    return new_g

  @staticmethod
  def make_node(kind=None, data=None):
    return Node(kind=kind, data=data)

  @staticmethod
  def make_edge(source=None, dest=None, kind=None, data=None):
    return Edge(source=source, dest=dest, kind=kind, data=data)


class Tree(object):
  def __init__(self):
    self._root = None

  @property
  def root(self):
    return self._root

  @root.setter
  def root(self, value):
    self._root = value

  def to_dot(self):
    from .io import DotConverter
    return DotConverter.process(self)


class TreeNode(object):
  GLOBAL_COUNTER = 0

  def __init__(self, kind=None, data=None):
    TreeNode.GLOBAL_COUNTER += 1
    self._id = TreeNode.GLOBAL_COUNTER
    self._kind = kind
    self._data = data
    self._children = list()

  @property
  def gid(self):
    return self._id

  @property
  def kind(self):
    return self._kind

  @kind.setter
  def kind(self, value):
    self._kind = value

  @property
  def data(self):
    return self._data

  @data.setter
  def data(self, value):
    self._data = value

  @property
  def children(self):
    return self._children

  def has_children(self):
    return len(self._children) > 0

  def num_children(self):
    return len(self._children)

  @property
  def first_child(self):
    return self._children[0]

  @property
  def last_child(self):
    return self._children[len(self._children) - 1]

  def child(self, n):
    return self._children[n]

  def reserve_children(self, number_children):
    self._children = [None] * number_children

  def insert_child(self, n, child):
    self._children[n] = child

  def __ne__(self, obj):
    return not self == obj

  def __eq__(self, obj):
    return isinstance(obj, TreeNode) and obj.gid == self.gid

  def __hash__(self):
    return hash('treenode-' + str(self.gid))

  def __repr__(self):
    return 'TreeNode%d(kind=%s, data=%s, num_children=%d)'  \
           % (self.gid, repr(self.kind), repr(self.data), self.num_children())
