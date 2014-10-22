# -*- coding: utf-8 -*-
"""
  equip.analysis.graph.io
  ~~~~~~~~~~~~~~~~~~~~~~~

  Outputs the graph structures

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
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
    self.buffer += 'digraph G {\nrankdir=TD;\n'

    for node in self.g.nodes:
      self.add_node(node)

    for edge in self.g.edges:
      self.add_edge(edge)

    self.buffer += '}\n'


  def add_edge(self, edge):
    labels = ''
    if edge.kind is not None:
      labels = '[label="%s"]' % edge.kind
    self.buffer += '%s -> %s %s;\n' % (self.get_node_id(edge.source), self.get_node_id(edge.dest), labels)


  def add_node(self, node):
    node_id = self.get_node_id(node)
    label = ''
    if node.data is not None:
      node_kind = ('%s - ' % node.kind) if node.kind is not None else ''
      label = '[label="Node%d - %s%s"]' % (node.gid, node_kind, node.data)
    self.buffer += '%s %s;\n' % (node_id, label)


  def get_node_id(self, node):
    if node not in self.node_ids:
      self.node_ids[node] = node.gid
    return 'node_%d' % self.node_ids[node]
