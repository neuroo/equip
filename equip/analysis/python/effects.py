# -*- coding: utf-8 -*-
"""
  equip.analysis.python.effects
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  Extracts information about stack effects of the opcodes.
  Leverages byteplay for the stack info.


  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""

import byteplay

def get_stack_effect(op, arg=None):
  """
    Returns the stack effect tuple (pop, push) for the given opcode/arg.

    :param op: The opcode.
    :param arg: Dereferenced argument of the opcode.
  """
  return byteplay.getse(op, arg)
