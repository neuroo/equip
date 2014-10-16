# -*- coding: utf-8 -*-
"""
  equip
  ~~~~~

  Bytecode instrumentation framework for Python.

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""

__version__ = '0.1'

import sys

if sys.version_info.major != 2 and sys.version_info.minor != 7:
  msg = ('Python version detected %d.%d not supported.'
      + ' Only supported version is 2.7') % (sys.version_info.major, sys.version_info.minor)
  raise Exception(msg)


from .prog import Program
from .instrument import Instrumentation
from .bytecode import BytecodeObject
from .rewriter import SimpleRewriter
from .visitors import MethodVisitor, \
                      ClassVisitor, \
                      ModuleVisitor, \
                      BytecodeVisitor

