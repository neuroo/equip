# -*- coding: utf-8 -*-
"""
  equip.analysis.ast.utils
  ~~~~~~~~~~~~~~~~~~~~~~~~

  Some static utils to work with Python AST nodes.

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""

from ast import *
from ...utils.log import logger

def dump_native_ast(node, annotate_fields=True, include_attributes=False, indent='  '):
  """
    Dumps the AST node in a pretty-printed format.
    Taken from http://greentreesnakes.readthedocs.org
  """
  if node is None:
    return "<None>"

  def _format(node, level=0):
    if isinstance(node, AST):
      fields = [(a, _format(b, level)) for a, b in iter_fields(node)]
      if include_attributes and node._attributes:
        fields.extend([(a, _format(getattr(node, a), level))
                 for a in node._attributes])
      return ''.join([
        node.__class__.__name__,
        '(',
        ', '.join(('%s=%s' % field for field in fields)
               if annotate_fields else
               (b for a, b in fields)),
        ')'])
    elif isinstance(node, list):
      lines = ['[']
      lines.extend((indent * (level + 2) + _format(x, level + 2) + ','
             for x in node))
      if len(lines) > 1:
        lines.append(indent * (level + 1) + ']')
      else:
        lines[-1] += ']'
      return '\n'.join(lines)
    return repr(node)

  if not isinstance(node, AST):
    raise TypeError('expected AST, got %r' % node.__class__.__name__)
  return _format(node)


def split_assignment(stmt_node):
  """
    Takes a ``Assign`` or ``AugAssign`` AST node, and split it into
    store expressions (expanded targets) and value.
  """
  is_assign = isinstance(stmt_node, Assign)
  is_aug_assign = isinstance(stmt_node, AugAssign)

  store_expr = list()
  load_expr = None

  if is_assign or is_aug_assign:
    if is_assign:
      targets = stmt_node.targets
      if isinstance(targets, Tuple) or isinstance(targets, List):
        for elmt in targets.elts:
          store_expr.append(elmt)
      else:
        for elmt in targets:
          store_expr.append(elmt)
    else:
      store_expr.append(stmt_node.target)

    # Process value
    load_expr = stmt_node.value

  return store_expr, load_expr


def serialize_name_attr(expr_node):
  """
    Takes a ``Name`` or ``Attribute`` AST node, and serialize it into
    a string representation.
  """
  if isinstance(expr_node, Name):
    return expr_node.id
  elif isinstance(expr_node, Attribute):
    # Walk back to the non-Attribute and '.' join the notation
    path = []
    cur = expr_node
    while True:
      if isinstance(cur, Attribute):
        path.insert(0, cur.attr)
        cur = cur.value
      elif isinstance(cur, Name):
        path.insert(0, cur.id)
        break
      elif isinstance(cur, Subscript) or isinstance(cur, Slice) or isinstance(cur, ExtSlice):
        cur = cur.value
      else:
        logger.error("Not handled node: %s", cur)
    return '.'.join(path)


def named_expr_iterator(node):
  """
    Returns a generator over the nested named expression (``Name`` or ``Attribute``).
  """
  if isinstance(node, Name) or isinstance(node, Attribute):
    yield node
  elif isinstance(node, AST):
    for attr_name, attr_value in iter_fields(node):
      for na in named_expr_iterator(attr_value):
        yield na
  elif isinstance(node, list):
    for n in node:
      for na in named_expr_iterator(n):
        yield na


def contained_expr(container, ast_expr):
  """
    Given a container, returns structural AST expression matches.
  """
  res = set()
  for elmt in container:
    if matches_expr(elmt, ast_expr):
      res.add(elmt)
  return list(res)


def matches_expr(ast_expr1, ast_expr2):
  """
    Compares 2 ``Expr`` nodes. Returns true if they are homomorphic (1 -> 2).
  """
  if type(ast_expr1) != type(ast_expr2):
    return False
  if isinstance(ast_expr1, Name) or isinstance(ast_expr1, Attribute):
    return serialize_name_attr(ast_expr1) == serialize_name_attr(ast_expr2)
  else:
    ret = True
    worklist = [(ast_expr1, ast_expr2)]
    while worklist:
      finger1, finger2 = worklist.pop(0)
      if type(finger1) != type(finger2):
        ret = False
        break
      for field_name in finger1._fields:
        field_value_1 = getattr(finger1, field_name)
        field_value_2 = getattr(finger2, field_name)

        if isinstance(field_value_1, AST):
          type_field = type(field_value_1)
          # We do not consider the context in the AST...
          if type_field not in (Load, Store, Del):
            worklist.append((field_value_1, field_value_2))
        else:
          # Scalar in the grammar
          if field_value_1 != field_value_2:
            ret = False
            break
      if not ret:
        break
    return ret


