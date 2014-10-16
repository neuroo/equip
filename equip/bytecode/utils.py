# -*- coding: utf-8 -*-
"""
  equip.bytecode.utils
  ~~~~~~~~~~~~~~~~~~~~

  Utilities for bytecode interaction.

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""
import opcode
import types
import dis
from opcode import *
from opcode import __all__ as _opcodes_all

from ..utils.log import logger


# Look into the main_co if we get orignal_co, if so we replace it with new_co
def update_nested_code_object(main_co, original_co, new_co):
  if not main_co:
    return
  logger.debug("Looking in main %s, replace by %s" % (original_co, new_co))

  main_co_consts = main_co.co_consts
  co_index = -1
  for co_const in main_co_consts:
    if not isinstance(co_const, types.CodeType):
      continue
    if co_const == original_co:
      co_index = main_co_consts.index(co_const)
      break

  if co_index < 0:
    logger.debug("Cannot find %s in main_co: %s" % (original_co, main_co_consts))
    return main_co

  new_co_consts = main_co.co_consts[:co_index] + (new_co,) + main_co.co_consts[co_index + 1:]
  main_co = types.CodeType(main_co.co_argcount, main_co.co_nlocals,
                           main_co.co_stacksize, main_co.co_flags,
                           main_co.co_code, new_co_consts,
                           main_co.co_names, main_co.co_varnames,
                           main_co.co_filename, main_co.co_name,
                           main_co.co_firstlineno, main_co.co_lnotab,
                           main_co.co_freevars, main_co.co_cellvars)

  logger.debug("Created new CO: %s" % main_co)
  return main_co


def show_bytecode(bytecode, start=0, end=2**32):
  buffer = []
  j = start
  end = min(end, len(bytecode) - 1)
  while j <= end:
    index, lineno, op, arg, _, co = bytecode[j]
    if op >= opcode.HAVE_ARGUMENT:
      rts = repr(arg)
      if len(rts) > 30:
        rts = rts[:30] + '[...]'
      jump_target = ''
      if op in opcode.hasjrel:
        jump_target = ' -------------> (%3d)' % (index + arg + 3)

      buffer.append("%3d(%3d) %20s(%3d) (%s)%s"
                    % (lineno, index, opcode.opname[op], op, rts, jump_target))
    else:
      buffer.append("%3d(%3d) %20s(%3d)"
                    % (lineno, index, opcode.opname[op], op))
    j += 1
  return '\n'.join(buffer)


CO_FIELDS = ('co_argcount', 'co_cellvars', 'co_consts', 'co_filename',
             'co_firstlineno', 'co_flags', 'co_freevars', 'co_lnotab', 'co_name',
             'co_names', 'co_nlocals', 'co_stacksize', 'co_varnames')


def get_debug_code_object_info(code_object):
  buffer = []
  for field in CO_FIELDS:
    field_name = field.replace('co_', '')
    val = getattr(code_object, field)
    buffer.append("%s := %s" % (field_name, val))
  return '\n'.join(buffer)


def get_debug_code_object_dict(code_object):
  dct = {}
  for field in CO_FIELDS:
    val = getattr(code_object, field)
    dct[field] = val
  return dct

