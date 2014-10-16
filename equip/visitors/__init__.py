# -*- coding: utf-8 -*-
"""
  equip.visitors
  ~~~~~~~~~~~~~~

  Different visitor interfaces to traverse the bytecode, modules,
  classes, or methods.

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""
from .bytecode import BytecodeVisitor
from .classes import ClassVisitor
from .methods import MethodVisitor
from .modules import ModuleVisitor
