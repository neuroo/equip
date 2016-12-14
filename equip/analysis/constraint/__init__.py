# -*- coding: utf-8 -*-
"""
  equip.analysis.constraint
  ~~~~~~~~~~~~~~~~~~~~~~~~~

  Represent code constraints.

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""

from .container import Constraint
from .expr import Expr, \
                  Const, \
                  Ref, \
                  Comparator, \
                  Operator, \
                  Undef
