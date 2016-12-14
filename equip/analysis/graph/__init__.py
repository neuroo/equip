# -*- coding: utf-8 -*-
"""
  equip.analysis.graph
  ~~~~~~~~~~~~~~~~~~~~

  Graph based operators.

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""

from .graphs import DiGraph, Edge, Node, Tree, TreeNode
from .traversals import Walker, EdgeVisitor
from .dominators import DominatorTree
from .dependences import ControlDependence
