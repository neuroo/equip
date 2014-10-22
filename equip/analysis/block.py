# -*- coding: utf-8 -*-
"""
  equip.analysis.block
  ~~~~~~~~~~~~~~~~~~~~

  Basic block for the bytecode.

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""


class BasicBlock(object):
  """
    Represents a basic block from the bytecode.
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

  @property
  def kind(self):
    return self._kind

  @kind.setter
  def kind(self, value):
    self._kind = value

  @property
  def decl(self):
    return self._decl

  @decl.setter
  def decl(self, value):
    self._decl = value

  @property
  def index(self):
    return self._index

  @index.setter
  def index(self, value):
    self._index = value

  @property
  def length(self):
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
    return self._jumps

  def clear_jumps(self):
    self._jumps = set()

  def add_jump(self, jump_index, branch_kind):
    self._jumps.add((jump_index, branch_kind))

  @property
  def end_target(self):
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
