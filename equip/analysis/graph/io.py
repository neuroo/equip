# -*- coding: utf-8 -*-
"""
  equip.analysis.graph.io
  ~~~~~~~~~~~~~~~~~~~~~~~

  Outputs the graph structures

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""

from .graphs import DiGraph, Tree

DOT_STYLE = """
rankdir=TD; ordering=out;
graph[fontsize=10 fontname="Verdana"];
color="#efefef";
node[shape=box style=filled fontsize=8 fontname="Verdana" fillcolor="#efefef"];
edge[fontsize=8 fontname="Verdana"];
"""

class DotConverter(object):
  def __init__(self, graph):
    self.g = graph
    self.buffer = ''
    self.node_ids = {}

  @staticmethod
  def process(graph):
    converter = DotConverter(graph)
    converter.run()
    return converter.buffer

  def run(self):
    self.buffer += 'digraph G {'
    self.buffer += DOT_STYLE

    if isinstance(self.g, DiGraph):
      for edge in self.g.edges:
        self.add_edge(edge)

    elif isinstance(self.g, Tree):
      root = self.g.root
      worklist = [root]

      while worklist:
        current = worklist.pop(0)
        if current.has_children():
          num_children = current.num_children()
          i = 0
          while i < num_children:
            child = current.children[i]
            if child is None:
              i += 1
              continue
            self.add_tree_edge(current, child)
            worklist.insert(0, child)
            i += 1
        else:
          nid = self.get_node_id(current)

    self.buffer += '}\n'


  def add_edge(self, edge):
    labels = ''
    if edge.kind is not None:
      data = '' if edge.data is None else str(edge.data)
      labels = '[label="%s - %s"]' % (edge.kind, data)

    nid1 = self.get_node_id(edge.source)
    nid2 = self.get_node_id(edge.dest)

    self.buffer += '%s -> %s %s;\n' % (nid1, nid2, labels)

  def add_tree_edge(self, node1, node2):
    nid1 = self.get_node_id(node1)
    nid2 = self.get_node_id(node2)
    self.buffer += '%s -> %s;\n' % (nid1, nid2)


  def get_node_id(self, node):
    if node not in self.node_ids:
      self.node_ids[node] = 'node_%d' % node.gid
      self.add_node(node, self.node_ids[node])
    return self.node_ids[node]

  def add_node(self, node, node_id):
    label = ''
    if node.data is not None:
      node_kind = ('%s - ' % node.kind) if node.kind is not None else ''
      label = '[label="Node%d - %s%s"]' % (node.gid, node_kind, node.data)
    self.buffer += '%s %s;\n' % (node_id, label)
