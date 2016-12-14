# -*- coding: utf-8 -*-
"""
  equip.analysis.block
  ~~~~~~~~~~~~~~~~~~~~

  Basic block for the bytecode.

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""

from .ast import Statement

class BasicBlock(object):
  """
    Represents a basic block from the bytecode. It's a bit more than just
    the location in the bytecode since it also contains the jump targets
    which are used during the construction of the control flow graph.
  """
  ENTRY = 1
  IMPLICIT_RETURN = 2
  UNKNOWN = 3
  LOOP = 4
  IF = 5
  EXCEPT = 6

  def __init__(self, kind, decl, index):
    self._kind = kind
    self._decl = decl
    self._index = index
    self._length = 0
    self._jumps = set()
    self._end_target = -1
    self._fallthrough = False
    self._has_return_path = False
    self._bytecode = None
    self._statements = None

  @property
  def kind(self):
    """
      Returns the kind of basic block.
    """
    return self._kind

  @kind.setter
  def kind(self, value):
    self._kind = value

  @property
  def decl(self):
    """
      Returns the ``Declaration`` associated to this basic block.
    """
    return self._decl

  @decl.setter
  def decl(self, value):
    self._decl = value

  @property
  def index(self):
    """
      Returns the start index (in the bytecode) for this basic block.
    """
    return self._index

  @index.setter
  def index(self, value):
    self._index = value

  @property
  def bytecode(self):
    """
      Returns the bytecode associated to this basic block.
    """
    if self._bytecode is None:
      if self.kind in (BasicBlock.ENTRY, BasicBlock.IMPLICIT_RETURN):
        self._bytecode = []
      else:
        bc = self.decl.bytecode
        start_index = [j for j in range(len(bc)) if bc[j][0] == 0][0]
        prev_co = bc[start_index][5]
        slice_bytecode = [tpl for tpl in bc[start_index:] if tpl[5] == prev_co]
        bc = []
        for l in slice_bytecode:
          idx = l[0]
          if idx >= self._index and idx < self._index + self._length:
            bc.append(l)
        self._bytecode = bc
    return self._bytecode

  @property
  def statements(self):
    if self._statements is None:
      from .flow import ControlFlow
      self._statements = []
      ControlFlow.create_statements(self, self.bytecode, self._statements)
    return self._statements

  @property
  def length(self):
    """
      Returns the length of the basic block (size of all the instructions)
    """
    return self._length

  @length.setter
  def length(self, value):
    assert value >= 0
    self._length = value

  @property
  def fallthrough(self):
    return self._fallthrough

  @fallthrough.setter
  def fallthrough(self, value):
    self._fallthrough = value

  @property
  def has_return_path(self):
    return self._has_return_path

  @has_return_path.setter
  def has_return_path(self, value):
    self._has_return_path = value

  @property
  def jumps(self):
    """
      Returns the list of all the targets from this basic block.
    """
    return self._jumps

  def clear_jumps(self):
    self._jumps = set()

  def add_jump(self, jump_index, branch_kind):
    self._jumps.add((jump_index, branch_kind))

  @property
  def end_target(self):
    """
      Returns the end of scope of the target. This is only meaningful for
      a loop or ``with``.
    """
    return self._end_target

  @end_target.setter
  def end_target(self, value):
    self._end_target = value

  def __repr__(self):
    end_target = ''
    if self.end_target > -1:
      end_target = ', target=%d' % self.end_target
    return 'BasicBlock(%s, %d->%d, jumps=%s%s)' \
           % (self.kind, self.index, (self.index + self.length), self.jumps, end_target)

