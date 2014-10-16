# -*- coding: utf-8 -*-
"""
  equip.visitors.bytecode
  ~~~~~~~~~~~~~~~~~~~~~~~

   Callback the visitor method for each encountered opcode.

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""

import opcode
from ..utils.log import logger


class BytecodeVisitor(object):
  """
    A visitor to visit each instruction in the bytecode. For example,
    the following code::

      class CallFunctionVisitor(BytecodeVisitor):
        def __init__(self):
          BytecodeVisitor.__init__(self)

        def visit_call_function(self, oparg):
          print "Function call with %d args" % oparg

    Prints whenever a ``CALL_FUNCTION`` opcode is visited and prints out
    its number of arguments (the oparg for this opcode).
  """

  def __init__(self):
    pass

  @staticmethod
  def toMethodName(name):
    return 'visit_' + name.lower().replace('+', '_')


  def visit(self, index, op, arg=None, lineno=None, cflow_in=False):
    """
      Callback of the visitor. It dynamically constructs the name
      of the specialized visitor to call based on the name of the opcode.

      :param index: Bytecode index.
      :param op: The opcode that is currently visited.
      :param arg: The expanded oparg (i.e., constants, names, etc. are resolved).
      :param lineno: The line number associated with the opcode.
      :param cflow_in: ``True`` if the current ``index`` is the target of a jump.
    """
    # Let's start with a slow impl of the jump table, with
    # reflection
    method_name = BytecodeVisitor.toMethodName(opcode.opname[op])
    if hasattr(self, method_name):
      meth = getattr(self, method_name)
      if op < opcode.HAVE_ARGUMENT:
        logger.debug("%03d %26s" % (lineno, method_name))
        return meth()
      else:
        logger.debug("%03d %26s( %s )" % (lineno, method_name, repr(arg)))
        return meth(arg)
    else:
      logger.error("Method not found: %s" % method_name)


  # 2.7 specific visitors. See https://docs.python.org/2/library/dis.html

  def visit_stop_code(self):
    pass

  def visit_pop_top(self):
    pass

  def visit_rot_two(self):
    pass

  def visit_rot_three(self):
    pass

  def visit_dup_top(self):
    pass

  def visit_rot_four(self):
    pass

  def visit_nop(self):
    pass

  def visit_unary_positive(self):
    pass

  def visit_unary_negative(self):
    pass

  def visit_unary_not(self):
    pass

  def visit_unary_convert(self):
    pass

  def visit_unary_invert(self):
    pass

  def visit_binary_power(self):
    pass

  def visit_binary_multiply(self):
    pass

  def visit_binary_divide(self):
    pass

  def visit_binary_modulo(self):
    pass

  def visit_binary_add(self):
    pass

  def visit_binary_subtract(self):
    pass

  def visit_binary_subscr(self):
    pass

  def visit_binary_floor_divide(self):
    pass

  def visit_binary_true_divide(self):
    pass

  def visit_inplace_floor_divide(self):
    pass

  def visit_inplace_true_divide(self):
    pass

  def visit_slice_0(self):
    pass

  def visit_slice_1(self):
    pass

  def visit_slice_2(self):
    pass

  def visit_slice_3(self):
    pass

  def visit_store_slice_0(self):
    pass

  def visit_store_slice_1(self):
    pass

  def visit_store_slice_2(self):
    pass

  def visit_store_slice_3(self):
    pass

  def visit_delete_slice_0(self):
    pass

  def visit_delete_slice_1(self):
    pass

  def visit_delete_slice_2(self):
    pass

  def visit_delete_slice_3(self):
    pass

  def visit_store_map(self):
    pass

  def visit_inplace_add(self):
    pass

  def visit_inplace_subtract(self):
    pass

  def visit_inplace_multiply(self):
    pass

  def visit_inplace_divide(self):
    pass

  def visit_inplace_modulo(self):
    pass

  def visit_store_subscr(self):
    pass

  def visit_delete_subscr(self):
    pass

  def visit_binary_lshift(self):
    pass

  def visit_binary_rshift(self):
    pass

  def visit_binary_and(self):
    pass

  def visit_binary_xor(self):
    pass

  def visit_binary_or(self):
    pass

  def visit_inplace_power(self):
    pass

  def visit_get_iter(self):
    pass

  def visit_print_expr(self):
    pass

  def visit_print_item(self):
    pass

  def visit_print_newline(self):
    pass

  def visit_print_item_to(self):
    pass

  def visit_print_newline_to(self):
    pass

  def visit_inplace_lshift(self):
    pass

  def visit_inplace_rshift(self):
    pass

  def visit_inplace_and(self):
    pass

  def visit_inplace_xor(self):
    pass

  def visit_inplace_or(self):
    pass

  def visit_break_loop(self):
    pass

  def visit_with_cleanup(self):
    pass

  def visit_load_locals(self):
    pass

  def visit_return_value(self):
    pass

  def visit_import_star(self):
    pass

  def visit_exec_stmt(self):
    pass

  def visit_yield_value(self):
    pass

  def visit_pop_block(self):
    pass

  def visit_end_finally(self):
    pass

  def visit_build_class(self):
    pass

  #
  # Opcode with arguments bellow
  #

  def visit_store_name(self, name): # name_op
    pass

  def visit_delete_name(self, name): # name_op
    pass

  def visit_unpack_sequence(self, oparg):
    pass

  def visit_for_iter(self, jump_rel): # jrel
    pass

  def visit_list_append(self, oparg):
    pass

  def visit_store_attr(self, name): # name_op
    pass

  def visit_delete_attr(self, name): # name_op
    pass

  def visit_store_global(self, name): # name_op
    pass

  def visit_delete_global(self, name): # name_op
    pass

  def visit_dup_topx(self, oparg):
    pass

  def visit_load_const(self, constant): # hasconst
    pass

  def visit_load_name(self, name): # name_op
    pass

  def visit_build_tuple(self, oparg):
    pass

  def visit_build_list(self, oparg):
    pass

  def visit_build_set(self, oparg):
    pass

  def visit_build_map(self, oparg):
    pass

  def visit_load_attr(self, name): # name attr
    pass

  def visit_compare_op(self, compare): # hascompare
    pass

  def visit_import_name(self, name): # name_op
    pass

  def visit_import_from(self, name): # name_op
    pass

  def visit_jump_forward(self, jump_rel): # jrel
    pass

  def visit_jump_if_false_or_pop(self, jump_abs): # jabs
    pass

  def visit_jump_if_true_or_pop(self, jump_abs): # jabs
    pass

  def visit_jump_absolute(self, jump_abs): # jabs
    pass

  def visit_pop_jump_if_false(self, jump_abs): # jabs
    pass

  def visit_pop_jump_if_true(self, jump_abs): # jabs
    pass

  def visit_load_global(self, name): # name_op
    pass

  def visit_continue_loop(self, jump_abs): # jabs
    pass

  def visit_setup_loop(self, jump_rel): # jrel
    pass

  def visit_setup_except(self, jump_rel): # jrel
    pass

  def visit_setup_finally(self, jump_rel): # jrel
    pass

  def visit_load_fast(self, local): # haslocal
    pass

  def visit_store_fast(self, local): # haslocal
    pass

  def visit_delete_fast(self, local): # haslocal
    pass

  def visit_raise_varargs(self, oparg):
    pass

  def visit_call_function(self, oparg):
    pass

  def visit_make_function(self, oparg):
    pass

  def visit_build_slice(self, oparg):
    pass

  def visit_make_closure(self, oparg):
    pass

  def visit_load_closure(self, free): # hasfree
    pass

  def visit_load_deref(self, free): # hasfree
    pass

  def visit_store_deref(self, free): # hasfree
    pass

  def visit_call_function_var(self, oparg):
    pass

  def visit_call_function_kw(self, oparg):
    pass

  def visit_call_function_var_kw(self, oparg):
    pass

  def visit_setup_with(self, jump_rel): # jrel
    pass

  def visit_extended_arg(self, oparg):
    pass

  def visit_set_add(self, oparg):
    pass

  def visit_map_add(self, oparg):
    pass
