# -*- coding: utf-8 -*-
"""
  equip.analysis.call
  ~~~~~~~~~~~~~~~~~~~

  Extract the control flow graphs from the bytecode.

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""
import opcode
from ..utils.log import logger

from .graph import DiGraph, Edge, Node, Walker, EdgeVisitor
from .flow import ControlFlow
from .block import BasicBlock
from .defs import DefUse

from .python.opcodes import *

from ..bytecode.decl import ModuleDeclaration, \
                            MethodDeclaration, \
                            TypeDeclaration
from ..bytecode.utils import iter_decl, show_bytecode


class CallNode(object):
  """
    A node-data in the call graph
  """
  GLOBAL_COUNTER = 0

  def __init__(self, name=None, parent_class=None, parent_module=None):
    Node.GLOBAL_COUNTER += 1
    self._id = Node.GLOBAL_COUNTER
    self._name = name
    self._is_method = parent_class is not None
    self._parent_class = parent_class
    self._parent_module = parent_module

  @property
  def gid(self):
    return self._id

  @property
  def name(self):
    return self._name

  @name.setter
  def name(self, value):
    self._name = value

  @property
  def is_method(self):
    return self._is_method

  @is_method.setter
  def is_method(self, value):
    self._is_method = value

  @property
  def parent_class(self):
    return self._parent_class

  @parent_class.setter
  def parent_class(self, value):
    self._parent_class = value

  @property
  def parent_module(self):
    return self._parent_module

  @parent_module.setter
  def parent_module(self, value):
    self._parent_module = value

  def __ne__(self, obj):
    return not self == obj

  def __eq__(self, obj):
    return isinstance(obj, CallNode) and obj.gid == self.gid

  def __hash__(self):
    return hash(self.gid)

  def __repr__(self):
    name = self.name
    if self.is_method:
      name = '%s.%s' % (parent_class.type_name, self.name)
    return 'CallNode%d(name=%s, module=%s)' % (self.gid, name, self.parent_module)



class CallGraph(object):
  """
    Holds a pessimistic call graph.
  """
  def __init__(self):
    self._graph = DiGraph(multiple_edges=False)
    self._defined_targets = {} # short name -> set(method declaration)
    self._block_calls = {}
    self._calls_targets = {}

  @property
  def defined_targets(self):
    return self._defined_targets

  @property
  def block_calls(self):
    return self._block_calls

  def register_type_method_name(self, decl):
    name = decl.method_name if isinstance(decl, MethodDeclaration) else decl.type_name
    if name not in self._defined_targets:
      self._defined_targets[name] = set()
    self._defined_targets[name].add(decl)

  def process(self, root_decl):
    """
      Process the given ``ModuleDeclaration`` and extract all call targets (best effort),
      to add to the global call graph.
    """
    block_cfg = {}
    resolve_vars = {}

    module = root_decl if isinstance(root_decl, ModuleDeclaration) else root_decl.parent_module
    for decl in iter_decl(root_decl):
      if isinstance(decl, MethodDeclaration) or isinstance(decl, TypeDeclaration):
        self.register_type_method_name(decl)

      cfg = ControlFlow(decl)
      cfg_blocks_calls = self.__find_calls(decl, cfg)
      self._block_calls.update(cfg_blocks_calls)

      def_use = DefUse(cfg)

    logger.debug("%s" % self._block_calls)




  def __find_calls(self, decl, cfg):
    cfg_blocks_calls = {}

    def get_call_arg_length(op, arg):
      na = arg & 0xff
      nk = (arg >> 8) & 0xff
      n = na + 2 * nk + CALL_EXTRA_ARG_OFFSET[op]
      return n

    def get_call_stack(bbl, index, op, arg, j, f2=None):
      n = get_call_arg_length(op, arg)
      if f2 is None:
        f2 = j - n - 1
      else:
        f2 -= n

      stack = []
      while f2 >= 0:
        cur_indx, cur_op, cur_arg = bytecode[f2][0], bytecode[f2][2], bytecode[f2][3]
        if cur_op not in LOAD_OPCODES:
          break
        cur_arg = bytecode[f2][3]
        stack.insert(0, cur_arg)
        if cur_op != LOAD_ATTR:
          break
        f2 -= 1

      if stack:
        map_block_call(bbl, index, stack)

      ret_index = 0
      # Recursive call (and moving the upward bytecode pointer) if this call was
      # an argument of another call.
      if j < length - 1 and bytecode[j + 1][2] in CALL_OPCODES:
        n_index, n_op, n_arg = bytecode[j + 1][0], bytecode[j + 1][2], bytecode[j + 1][3]
        ret_index += get_call_stack(bbl, n_index, n_op, n_arg, j + 1, f2) + 1
      return ret_index

    def map_block_call(bbl, index, stack):
      if bbl not in cfg_blocks_calls:
        cfg_blocks_calls[bbl] = {}
      cfg_blocks_calls[bbl][index] = stack

    for block in cfg.blocks:
      bytecode = block.bytecode
      length = len(bytecode)

      i = 0
      while i < length:
        index, lineno, op, arg, cflow_in, code_object = bytecode[i]

        # Skipping the CALL_FUNCTION, MAKE_FUNCTION
        if op in CALL_OPCODES and bytecode[i - 1][2] != MAKE_FUNCTION:
          # We then need to find the name of that function.
          if bytecode[i - 1][2] not in CALL_OPCODES:
            i += get_call_stack(block, index, op, arg, i)
        i += 1

    return cfg_blocks_calls
