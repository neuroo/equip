import pytest

import equip.utils.log as logutils
from equip.utils.log import logger
logutils.enableLogger(to_file='./equip.log')

from equip.analysis.graph import DiGraph, Node, Edge, Walker, EdgeVisitor
from equip.analysis.graph.traversals import dfs_postorder_nodes

def test_simple_graph():
  g = DiGraph()
  n1 = DiGraph.make_node(data='n1')
  n2 = DiGraph.make_node(data='n2')
  n3 = DiGraph.make_node(data='n3')
  n4 = DiGraph.make_node(data='n4')

  e12 = DiGraph.make_edge(source=n1, dest=n2)
  e13 = DiGraph.make_edge(source=n1, dest=n3)
  e14 = DiGraph.make_edge(source=n1, dest=n4)
  e24 = DiGraph.make_edge(source=n2, dest=n4)
  e34 = DiGraph.make_edge(source=n3, dest=n4)

  g.add_edge(e12)
  g.add_edge(e13)
  g.add_edge(e14)
  g.add_edge(e24)
  g.add_edge(e34)

  assert len(g.nodes) == 4
  assert len(g.edges) == 5

  assert g.in_degree(n1) == 0
  assert g.in_degree(n2) == 1
  assert g.in_degree(n3) == 1
  assert g.in_degree(n4) == 3

  assert g.out_degree(n1) == 3
  assert g.out_degree(n2) == 1
  assert g.out_degree(n3) == 1
  assert g.out_degree(n4) == 0

  assert e12 in g.in_edges(n2)
  assert e14 in g.in_edges(n4)
  assert e24 in g.in_edges(n4)
  assert e34 in g.in_edges(n4)

  assert e12 in g.out_edges(n1)
  assert e13 in g.out_edges(n1)
  assert e24 in g.out_edges(n2)
  assert e34 in g.out_edges(n3)
  assert e34 not in g.out_edges(n4)


def test_graph_manip():
  g = DiGraph()
  n1 = DiGraph.make_node(data='n1')
  n2 = DiGraph.make_node(data='n2')
  n3 = DiGraph.make_node(data='n3')
  n4 = DiGraph.make_node(data='n4')

  e12 = DiGraph.make_edge(source=n1, dest=n2)
  e13 = DiGraph.make_edge(source=n1, dest=n3)
  e14 = DiGraph.make_edge(source=n1, dest=n4)
  e24 = DiGraph.make_edge(source=n2, dest=n4)
  e34 = DiGraph.make_edge(source=n3, dest=n4)

  g.add_edge(e12)
  g.add_edge(e13)
  g.add_edge(e14)
  g.add_edge(e24)
  g.add_edge(e34)

  assert len(g.nodes) == 4

  g.remove_node(n1)

  assert len(g.nodes) == 3
  assert e12 not in g.edges
  assert e13 not in g.edges
  assert e14 not in g.edges

  g.remove_edge(e34)

  assert e34 not in g.edges
  assert e34 not in g.in_edges(n4)
  assert e24 in g.in_edges(n4)
  assert g.in_degree(n4) == 1

  g.remove_edge(e12)


def test_inverse_graph():
  g = DiGraph()
  n1 = DiGraph.make_node(data='n1')
  n2 = DiGraph.make_node(data='n2')
  n3 = DiGraph.make_node(data='n3')
  n4 = DiGraph.make_node(data='n4')

  e12 = DiGraph.make_edge(source=n1, dest=n2)
  e13 = DiGraph.make_edge(source=n1, dest=n3)
  e14 = DiGraph.make_edge(source=n1, dest=n4)
  e24 = DiGraph.make_edge(source=n2, dest=n4)
  e34 = DiGraph.make_edge(source=n3, dest=n4)

  g.add_edge(e12)
  g.add_edge(e13)
  g.add_edge(e14)
  g.add_edge(e24)
  g.add_edge(e34)
  g.freeze()

  logger.debug("Normal graph :=\n%s", g.to_dot())

  inv_g = g.inverse()
  logger.debug("Inverse graph :=\n%s", inv_g.to_dot())

  # Check equality of nodes in both graphs
  for g_node in g.nodes:
    has_equal = False
    for inv_node in inv_g.nodes:
      if g_node == inv_node:
        has_equal = True
        break
    assert has_equal


def test_walker():
  g = DiGraph()
  n1 = DiGraph.make_node(data='n1')
  n2 = DiGraph.make_node(data='n2')
  n3 = DiGraph.make_node(data='n3')
  n4 = DiGraph.make_node(data='n4')
  n5 = DiGraph.make_node(data='n5')
  n6 = DiGraph.make_node(data='n6')

  e12 = DiGraph.make_edge(source=n1, dest=n2)
  e13 = DiGraph.make_edge(source=n1, dest=n3)
  e14 = DiGraph.make_edge(source=n1, dest=n4)
  e24 = DiGraph.make_edge(source=n2, dest=n4)
  e34 = DiGraph.make_edge(source=n3, dest=n4)
  e45 = DiGraph.make_edge(source=n4, dest=n5)
  e56 = DiGraph.make_edge(source=n5, dest=n6)
  e61 = DiGraph.make_edge(source=n6, dest=n1) # add cycle

  g.add_edge(e12)
  g.add_edge(e13)
  g.add_edge(e14)
  g.add_edge(e24)
  g.add_edge(e34)
  g.add_edge(e45)
  g.add_edge(e56)
  g.add_edge(e61)

  class EdgePrinterVisitor(EdgeVisitor):
    def __init__(self):
      EdgeVisitor.__init__(self)
      self.edges = []

    def visit(self, edge):
      self.edges.append(edge)

  visitor = EdgePrinterVisitor()
  walker = Walker(g, visitor)
  walker.traverse(n1)

  logger.debug("Post-order DFS: %s", dfs_postorder_nodes(g, n1))


  assert len(visitor.edges) == 8

  logger.debug("\n" + g.to_dot())

  s = DiGraph()
  n1 = s.make_add_node(data='n1')
  n2 = s.make_add_node(data='n2')
  n3 = s.make_add_node(data='n3')
  e12 = s.make_add_edge(n1, n2)
  e23 = s.make_add_edge(n2, n3)
  logger.debug("Post-order DFS: %s", dfs_postorder_nodes(s, n1))





