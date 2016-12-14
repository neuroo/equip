# -*- coding: utf-8 -*-
"""
  equip.analysis.ast.stmt
  ~~~~~~~~~~~~~~~~~~~~~~~

  Minimal, high-level AST for the Python bytecode.

  Extra documentation from the _ast module can be found online:
    http://greentreesnakes.readthedocs.org/en/latest/nodes.html#statements

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""
import _ast, ast
import opcode
from ...utils.log import logger
from ...bytecode.utils import show_bytecode

from ..python.opcodes import *
from ..python.effects import get_stack_effect
from .utils import dump


class Statement(object):
  """
    A statement in the bytecode is a set of opcodes. The stack effect of the
    statement is zero. The kind of statement is a subset of what is possible
    from the Python grammar; this is due to the simplified representations.
  """
  def __init__(self, block, start_bytecode_index, end_bytecode_index):
    self._block = block
    self._start_bytecode_index = start_bytecode_index
    self._end_bytecode_index = end_bytecode_index
    self._native = None

  @property
  def block(self):
    return self._block

  @property
  def start_bytecode_index(self):
    return self._start_bytecode_index

  @start_bytecode_index.setter
  def start_bytecode_index(self, value):
    self._start_bytecode_index = value

  @property
  def end_bytecode_index(self):
    return self._end_bytecode_index

  @end_bytecode_index.setter
  def end_bytecode_index(self, value):
    self._end_bytecode_index = value

  @property
  def bytecode(self):
    return self.block.bytecode[self.start_bytecode_index : self.end_bytecode_index + 1]

  @property
  def native(self):
    if self._native is None:
      self._native = Statement.to_python_statment(self.bytecode)
    return self._native

  def __repr__(self):
    return 'Statement(parent=%s, %d->%d)' \
            % (self.block, self.start_bytecode_index, self.end_bytecode_index)

  @staticmethod
  def to_python_statment(bytecode):
    i = len(bytecode) - 1
    while i >= 0:
      index, lineno, op, arg, cflow_in, code_object = bytecode[i]
      prev_op = bytecode[i - 1][2] if i > 1 else -1
      if op in (PRINT_ITEM, PRINT_NEWLINE, PRINT_ITEM_TO, PRINT_NEWLINE_TO):
        _, stmt = Statement.to_print_statement(i, op, bytecode)
        return stmt
      elif op in CALL_OPCODES:
        _, call = Statement.make_call(i, bytecode)
        return _ast.Expr(call)
      elif op == COMPARE_OP:
        _, cmp_expr = Statement.make_comparator(i, bytecode)
        return _ast.Expr(cmp_expr)
      elif op in STORE_OPCODES and prev_op not in (MAKE_FUNCTION, BUILD_CLASS):
        _, store_stmt = Statement.make_assign(i, bytecode)
        return store_stmt
      elif op in STORE_SLICE_OPCODES or op in DELETE_SLICE_OPCODES:
        _, store_stmt = Statement.make_store_delete_slice(i, bytecode)
        return store_stmt
      elif op in DELETE_OPCODES:
        _, store_stmt = Statement.make_delete(i, bytecode)
        return store_stmt
      else:
        logger.debug("Unhandled >> STMT:\n%s", show_bytecode(bytecode))
      i -= 1
    return None


  @staticmethod
  def to_print_statement(i, op, bytecode):
    stmt = _ast.Print()
    stmt.nl = False
    if op in (PRINT_ITEM_TO, PRINT_NEWLINE_TO):
      logger.error("Print to not handled yet.")
      pass
    else:
      if op == PRINT_NEWLINE:
        stmt.nl = True
      else:
        i, expr = Statement.make_expr(i - 1, bytecode)
        stmt.values = expr
    return i, stmt


  UNDEFINED_COUNT = 0

  @staticmethod
  def make_expr(i, bytecode, context=None):
    if context is None:
      context = _ast.Load()

    op = bytecode[i][2]
    if op == LOAD_CONST:
      return Statement.make_const(i, bytecode)
    elif op in (LOAD_GLOBAL, LOAD_NAME, LOAD_FAST,        \
                STORE_GLOBAL, STORE_NAME, STORE_FAST,     \
                DELETE_GLOBAL, DELETE_NAME, DELETE_FAST):
      return Statement.make_name(i, bytecode, context=context)
    elif op in (LOAD_ATTR, STORE_ATTR, DELETE_ATTR):
      return Statement.make_attribute(i, bytecode, context=context)
    elif op in CALL_OPCODES:
      return Statement.make_call(i, bytecode)
    elif op in BINARY_OP_OPCODES:
      return Statement.make_binary_op(i, bytecode)
    elif op in (BUILD_TUPLE, BUILD_LIST):
      return Statement.make_tuple_list(i, bytecode)
    elif op in (STORE_MAP, BUILD_MAP):
      return Statement.make_dict(i, bytecode)
    elif op in (STORE_SUBSCR, BINARY_SUBSCR):
      return Statement.make_subscript(i, bytecode)
    elif op in STORE_SLICE_OPCODES or op in DELETE_SLICE_OPCODES:
      return Statement.make_store_delete_slice(i, bytecode)
    elif op == BUILD_SLICE:
      return Statement.make_slice(i, bytecode)

    logger.debug("Unhandled >> EXPR:\n%s", show_bytecode(bytecode[:i + 1]))

    # if we don't translate it, we generate a new named expr.
    Statement.UNDEFINED_COUNT += 1
    return i, _ast.Name('Undef_%d' % Statement.UNDEFINED_COUNT, _ast.Load())


  @staticmethod
  def make_call(i, bytecode):
    op = bytecode[i][2]

    def get_call_arg_length(op, arg):
      na = arg & 0xff         # num args
      nk = (arg >> 8) & 0xff  # num keywords
      return na, nk, na + 2 * nk + CALL_EXTRA_ARG_OFFSET[op]

    has_var, has_kw = 0, 0
    if op in (CALL_FUNCTION_VAR, CALL_FUNCTION_VAR_KW): has_var = 1
    if op in (CALL_FUNCTION_KW, CALL_FUNCTION_VAR_KW): has_kw = 1

    op, arg = bytecode[i][2], bytecode[i][3]
    num_args, num_keywords, offset = get_call_arg_length(op, arg)

    func, args, keywords, starargs, kwargs = None, None, None, None, None

    if has_kw > 0:
      i, kwargs = Statement.make_expr(i - 1, bytecode)

    if has_var > 0:
      i, starargs = Statement.make_expr(i - 1, bytecode)

    # Handle keywords
    if num_keywords > 0:
      keywords = []
      while num_keywords > 0:
        i, kw_value = Statement.make_expr(i - 1, bytecode)
        i, kw_name = Statement.make_expr(i - 1, bytecode)
        keywords.insert(0, _ast.keyword(kw_name, kw_value))
        num_keywords -= 1

    finger = i - 1

    if num_args > 0:
      n = num_args - 1
      args = [None] * num_args
      for k in range(num_args):
        cur_stack = 0
        loc_bytecode = []
        is_first = True
        while True:
          op, arg = bytecode[finger][2], bytecode[finger][3]
          pop, push = get_stack_effect(op, arg)
          cur_stack -= (pop - push) if not is_first else pop
          is_first = False
          loc_bytecode.insert(0, bytecode[finger])
          if cur_stack == 0:
            break
          finger -= 1
        _, args[n] = Statement.make_expr(len(loc_bytecode) - 1, loc_bytecode)
        n -= 1
        finger -= 1

    _, func = Statement.make_expr(finger, bytecode)

    call = _ast.Call(func, args, keywords, starargs, kwargs)
    logger.debug("\n%s", dump(call))
    return finger, call

  @staticmethod
  def make_delete(i, bytecode):
    logger.debug("Delete: \n%s", show_bytecode(bytecode))
    op = bytecode[i][2]
    if op == DELETE_SUBSCR:
      i, subscr_expr = Statement.make_subscript(i, bytecode, context=_ast.Del())
      return i, _ast.Delete([subscr_expr])
    else:
      i, attr_expr = Statement.make_expr(i, bytecode, context=_ast.Del())
      return i, _ast.Delete([attr_expr])

    return i, None


  INPLACE_OPERATORS = {
    INPLACE_FLOOR_DIVIDE: _ast.FloorDiv,
    INPLACE_TRUE_DIVIDE: _ast.Div,
    INPLACE_ADD: _ast.Add,
    INPLACE_SUBTRACT: _ast.Sub,
    INPLACE_MULTIPLY: _ast.Mult,
    INPLACE_DIVIDE: _ast.Div,
    INPLACE_MODULO: _ast.Mod,
    INPLACE_POWER: _ast.Pow,
    INPLACE_LSHIFT: _ast.LShift,
    INPLACE_RSHIFT: _ast.RShift,
    INPLACE_AND: _ast.BitAnd,
    INPLACE_XOR: _ast.BitXor,
    INPLACE_OR: _ast.BitOr,
  }

  @staticmethod
  def make_assign(i, bytecode):
    op = bytecode[i][2]
    if op == STORE_SUBSCR:
      return Statement.make_subscript(i, bytecode)

    prev_op = bytecode[i - 1][2] if i > 0 else -1

    if prev_op in INPLACE_OPCODES:
      in_cls = Statement.INPLACE_OPERATORS[prev_op]
      i -= 1
      i, rhs = Statement.make_expr(i - 1, bytecode, context=_ast.AugStore())
      i, lhs = Statement.make_expr(i - 1, bytecode, context=_ast.AugLoad())
      return i, _ast.AugAssign(lhs, in_cls(), rhs)
    else:
      # We can either have multiple assignments: a = b = c = 1
      # or unpacked sequences: a, b = 1, foo()
      # the compiler does some optimization so that: a, b = c, d
      # does not rely on UNPACK_SEQUENCE, but a ROT_TWO (or ROT_THREE & ROT_TWO for 3 elements).
      # This happens for 2 or 3 elements to unpack
      targets = []
      value = None
      has_unpack, has_ROT_2_3, has_multiple = False, False, 0
      num_unpack = -1
      j = i
      while j >= 0:
        op = bytecode[j][2]
        if op == UNPACK_SEQUENCE:
          has_unpack = True
          num_unpack = bytecode[j][3]
          break
        elif op in (ROT_TWO, ROT_THREE):
          has_ROT_2_3 = True
          break
        if op == DUP_TOP:
          has_multiple += 1
        j -= 1

      if has_unpack:
        return Statement.make_assign_unpack(i, bytecode, unpack_num=num_unpack)
      elif has_ROT_2_3:
        return Statement.make_assign_opt_unpack(i, bytecode)
      elif has_multiple > 0:
        return Statement.make_assign_chained(i, bytecode)
      else:
        # A simple assignment
        i, store_expr = Statement.make_expr(i, bytecode)
        i, value_expr = Statement.make_expr(i - 1, bytecode)
        return i, _ast.Assign([store_expr], value_expr)
    return i, None


  # 2 cases here:
  #  (1) a, b, c = foo() <=> v = foo(), a = v[0], b = v[1], c = v[2]
  #    => AST: _ast.Assign(targets=[Tuple(a, b, c)], value=foo())
  #
  #  (2) a, b = foo(), bar() <=> a = foo(), b = bar()
  #    => AST: _ast.Assign(targets=[Tuple(a, b)], value=Tuple(baz(), bar()))
  @staticmethod
  def make_assign_unpack(i, bytecode, unpack_num=-1):
    if unpack_num < 1:
      logger.error("Could not find the number of unpacked items. ")
      return i, None

    store_exprs = []
    value_exprs = []
    store_state, value_state = True, False

    while i >= 0:
      op, arg = bytecode[i][2], bytecode[i][3]
      if store_state:
        if op == UNPACK_SEQUENCE:
          store_state = False
          prev_op = bytecode[i - 1][2] if i > 0 else -1
          if prev_op == BUILD_TUPLE:
            value_state = True
          else:
            i, value_exprs = Statement.make_expr(i - 1, bytecode)
            break
        elif op in STORE_OPCODES:
          i, store_stmt = Statement.make_expr(i, bytecode, context=_ast.Store())
          store_exprs.insert(0, store_stmt)
      elif value_state:
        i, value_stmt = Statement.make_expr(i, bytecode)
        value_exprs.insert(0, value_stmt)

      i -= 1

    store_exprs = _ast.Tuple(store_exprs, _ast.Store())
    if not isinstance(value_exprs, _ast.AST):
      value_exprs = _ast.Tuple(value_exprs, _ast.Load())

    return i, _ast.Assign([store_exprs], value_exprs)


  @staticmethod
  def make_assign_opt_unpack(i, bytecode):
    store_exprs = []
    value_exprs = []
    store_state, value_state = True, False

    while i >= 0:
      op, arg = bytecode[i][2], bytecode[i][3]
      if store_state:
        if op == ROT_TWO:
          prev_op = bytecode[i - 1][2] if i > 0 else -1
          if prev_op == ROT_THREE:
            i -= 1
          value_state = True
          store_state = False
        elif op in STORE_OPCODES:
          i, store_stmt = Statement.make_expr(i, bytecode, context=_ast.Store())
          store_exprs.insert(0, store_stmt)
      elif value_state:
        i, value_stmt = Statement.make_expr(i, bytecode)
        value_exprs.insert(0, value_stmt)
      i -= 1

    store_exprs = _ast.Tuple(store_exprs, _ast.Store())
    if not isinstance(value_exprs, _ast.AST):
      value_exprs = _ast.Tuple(value_exprs, _ast.Load())

    return i, _ast.Assign([store_exprs], value_exprs)


  # Only one case here for:
  #   a = b = z.d.f = foo()
  #    => AST: _ast.Assign(targets=[Tuple(a, b, z.d.f)], value=foo())
  @staticmethod
  def make_assign_chained(i, bytecode):
    store_exprs = []
    value_exprs = []
    store_state, value_state = True, False

    while i >= 0:
      op, arg = bytecode[i][2], bytecode[i][3]
      if store_state:
        if op == DUP_TOP:
          prev_op = bytecode[i - 1][2] if i > 0 else -1
          if prev_op not in STORE_OPCODES:
            value_state = True
            store_state = False
        elif op in STORE_OPCODES:
          i, store_stmt = Statement.make_expr(i, bytecode, context=_ast.Store())
          store_exprs.insert(0, store_stmt)
      elif value_state:
        i, value_exprs = Statement.make_expr(i, bytecode)
        break
      i -= 1

    store_exprs = _ast.Tuple(store_exprs, _ast.Store())
    return i, _ast.Assign([store_exprs], value_exprs)


  CMP_OP_AST_NODE_MAP = {
    '<': _ast.Lt,
    '<=': _ast.LtE,
    '==': _ast.Eq,
    '!=': _ast.NotEq,
    '>': _ast.Gt,
    '>=': _ast.GtE,
    'in': _ast.In,
    'not in': _ast.NotIn,
    'is': _ast.Is,
    'is not': _ast.IsNot,
  }

  @staticmethod
  def make_comparator(i, bytecode):
    op, arg = bytecode[i][2], bytecode[i][3]
    if arg not in Statement.CMP_OP_AST_NODE_MAP:
      return Statement.make_exception(i, bytecode)

    cmp_op = Statement.CMP_OP_AST_NODE_MAP[arg]()
    i, rhs = Statement.make_expr(i - 1, bytecode)
    i, lhs = Statement.make_expr(i - 1, bytecode)
    comp_stmt = _ast.Compare(lhs, [cmp_op], [rhs])
    return i, comp_stmt


  @staticmethod
  def make_exception(i, bytecode):
    logger.error("Exception STMT not handled.")
    return i, None


  # Store slice has 4 opodes:
  #  (1) STORE_SLICE+0 => TOS[:] = TOS1
  #  (2) STORE_SLICE+1 => TOS1[TOS:] = TOS2
  #  (3) STORE_SLICE+2 => TOS1[:TOS] = TOS2
  #  (4) STORE_SLICE+3 => TOS2[TOS1:TOS] = TOS3
  @staticmethod
  def make_store_delete_slice(i, bytecode, context=None):
    op = bytecode[i][2]
    is_delete = op in DELETE_SLICE_OPCODES

    if context is None:
      context = _ast.Store() if not is_delete else _ast.Del()

    lhs_expr = None

    if op in (STORE_SLICE_0, DELETE_SLICE_0):
      i, lhs_expr = Statement.make_expr(i - 1, bytecode, context=context)
      lhs_expr = _ast.Subscript(lhs_expr,
                                _ast.Slice(None, None, None),
                                _ast.Store())
    elif op in (STORE_SLICE_1, STORE_SLICE_2, DELETE_SLICE_1, DELETE_SLICE_2):
      i, index_expr = Statement.make_expr(i - 1, bytecode)
      i, arr_expr = Statement.make_expr(i - 1, bytecode, context=context)

      args = [None] * 3
      index_index = 0 if op in (STORE_SLICE_1, DELETE_SLICE_1) else 1
      args[index_index] = index_expr
      lhs_expr = _ast.Subscript(arr_expr,
                                _ast.Slice(*args),
                                _ast.Store())
    else:
      i, end_index_expr = Statement.make_expr(i - 1, bytecode)
      i, start_index_expr = Statement.make_expr(i - 1, bytecode)
      i, arr_expr = Statement.make_expr(i - 1, bytecode, context=context)

      lhs_expr = _ast.Subscript(arr_expr,
                                _ast.Slice(start_index_expr, end_index_expr, None),
                                _ast.Store())

    if is_delete:
      return i, _ast.Delete([lhs_expr])
    else:
      i, rhs_expr = Statement.make_expr(i - 1, bytecode)
      return i, _ast.Assign([lhs_expr], rhs_expr)


  @staticmethod
  def make_slice(i, bytecode):
    i, step_expr = Statement.make_expr(i - 1, bytecode)
    i, upper_expr = Statement.make_expr(i - 1, bytecode)
    i, lower_expr = Statement.make_expr(i - 1, bytecode)
    return i, _ast.Slice(lower_expr, upper_expr, step_expr)


  @staticmethod
  def make_subscript(i, bytecode, context=None):
    op = bytecode[i][2]
    if op == STORE_SUBSCR:
      # TOS1[TOS] = TOS2
      i, index_expr = Statement.make_expr(i - 1, bytecode)
      i, arr_expr = Statement.make_expr(i - 1, bytecode, context=_ast.Store())
      i, rhs_expr = Statement.make_expr(i - 1, bytecode)
      lhs_expr = _ast.Subscript(arr_expr, index_expr, _ast.Store())
      return i, _ast.Assign([lhs_expr], rhs_expr)
    else:
      if context is None:
        context = _ast.Load()

      # BINARY_SUBSCR: TOS1[TOS] and DELETE_SUBSCR TOS1[TOS]
      i, index_expr = Statement.make_expr(i - 1, bytecode)
      i, arr_expr = Statement.make_expr(i - 1, bytecode)
      return i, _ast.Subscript(arr_expr, index_expr, context)


  BIN_OP_AST_NODE_MAP = {
    BINARY_OR: _ast.BitOr,
    BINARY_XOR: _ast.BitXor,
    BINARY_AND: _ast.BitAnd,
    BINARY_RSHIFT: _ast.RShift,
    BINARY_LSHIFT: _ast.LShift,
    BINARY_SUBTRACT: _ast.Sub,
    BINARY_ADD: _ast.Add,
    BINARY_MODULO: _ast.Mod,
    BINARY_DIVIDE: _ast.Div,
    BINARY_MULTIPLY: _ast.Mult,
    BINARY_POWER: _ast.Pow,
    BINARY_FLOOR_DIVIDE: _ast.FloorDiv,
    BINARY_TRUE_DIVIDE: _ast.Div,
  }

  @staticmethod
  def make_binary_op(i, bytecode):
    op = bytecode[i][2]
    bin_op = Statement.BIN_OP_AST_NODE_MAP[op]()
    i, rhs = Statement.make_expr(i - 1, bytecode)
    i, lhs = Statement.make_expr(i - 1, bytecode)
    return i, _ast.BinOp(lhs, bin_op, rhs)


  # Build Attr(value=Attr(value=Name(id=a), attr=b), attr=c) <=> a.b.c
  @staticmethod
  def make_attribute(i, bytecode, context=None):
    arg = bytecode[i][3]
    attr_path = []
    j = i
    while True:
      prev_op, prev_arg =  bytecode[j][2], bytecode[j][3]
      if prev_op not in (LOAD_ATTR, STORE_ATTR, DELETE_ATTR):
        break
      attr_path.append(prev_arg)
      if j < 0:
        break
      j -= 1
    # The parent of the ATTR can be whatever expression...
    i, name = Statement.make_expr(j, bytecode)
    attr = name
    while True:
      if not attr_path:
        break
      attr_name = attr_path.pop()
      attr = _ast.Attribute(attr, attr_name, context)
    return i, attr


  @staticmethod
  def make_name(i, bytecode, context=None):
    arg = bytecode[i][3]
    if context is None:
      context = _ast.Load()
    return i, _ast.Name(arg, context)


  @staticmethod
  def make_tuple_list(i, bytecode):
    op, arg = bytecode[i][2], bytecode[i][3]
    pop, push = get_stack_effect(op, arg)
    values = []
    for k in range(pop):
      i, expr = Statement.make_expr(i - 1, bytecode)
      values.insert(0, expr)
    cls = _ast.Tuple if op == BUILD_TUPLE else _ast.List
    return i, cls(values, _ast.Load())


  @staticmethod
  def make_dict(i, bytecode):
    """
      This is a trick. We don't try to resolve exactly what the dict
      contains, but just create a dict type with the proper number of args.
    """
    logger.debug("i=%d, bytecode=\n%s", i, show_bytecode(bytecode))
    num_keys = -1
    if bytecode[i][2] == BUILD_MAP:
      return i, _ast.Dict([], [])
    else:
      keys, values = [], []
      j = i - 1
      build_map_idx = i - 1
      while j >= 0:
        if bytecode[j][2] == BUILD_MAP:
          num_keys = bytecode[j][3]
          build_map_idx = j
        j -= 1
      return build_map_idx, _ast.Dict(range(num_keys), [None] * num_keys)

    return build_map_idx, None


  @staticmethod
  def make_const(i, bytecode):
    arg = bytecode[i][3]
    if isinstance(arg, basestring):
      return i, _ast.Str(arg)
    elif isinstance(arg, int) or isinstance(arg, float) or isinstance(arg, long):
      return i, _ast.Num(arg)
    elif isinstance(arg, dict):
      return i, _ast.Dict(arg.keys(), arg.values())
    elif isinstance(arg, set):
      return i, _ast.Dict(arg)
    elif isinstance(arg, tuple):
      return i, _ast.Tuple(arg, _ast.Load())
    elif isinstance(arg, list):
      return i, _ast.List(arg, _ast.Load())
    elif isinstance(arg, bytes):
      return i, _ast.Bytes(arg)
    return i, None

