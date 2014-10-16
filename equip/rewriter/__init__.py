# -*- coding: utf-8 -*-
"""
  equip.rewriter
  ~~~~~~~~~~~~~~

  Utilities to merge and rewrite the bytecode.

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""

from .merger import Merger, RETURN_CANARY_NAME
from .simple import SimpleRewriter
