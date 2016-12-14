# -*- coding: utf-8 -*-
"""
  equip.analysis.dfg
  ~~~~~~~~~~~~~~~~~~~

  Builds a dataflow graph.

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""


from .graph import DiGraph, Edge, Node, Walker, EdgeVisitor
from ..bytecode.decl import MethodDeclaration



class DataflowGraph(object):
  N_UNKNOWN = -1
  N_JOIN = 0
  N_PARAM = 1
  N_RETURN = 2
  N_CHOICE = 3
  N_PROPERTY = 4
  N_READ = 5
  N_WRITE = 6
  N_CONST = 7
  N_CALL = 8

  E_UNKNOWN = -1
  E_ARG = 0
  E_CALL = 1

  def __init__(self, decl, cfg):
    self._decl = decl
    self._cfg = cfg
    self._graph = None

  @property
  def decl(self):
    return self._decl

  @property
  def cfg(self):
    return self._cfg

  def build(self):
    if not isinstance(self.decl, MethodDeclaration):
      raise Exception("Can only build DFG for a function")
    self._graph = DiGraph(multiple_edges=False)

    self.__add_formal_structure()
    self.__transfer_statements()


  def __transfer_statements(self):
    start_node = self.cfg.entry_node



  def __add_formal_structure(self):
    for formal_param in self.decl.formal_parameters:
      self._graph.make_add_node(kind=DataflowGraph.N_PARAM, data=self._decl)
    self._graph.make_add_node(kind=DataflowGraph.N_RETURN, data=self._decl)
