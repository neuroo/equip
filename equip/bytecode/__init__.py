# -*- coding: utf-8 -*-
"""
  equip.bytecode
  ~~~~~~~~~~~~~~

  Operations and representations related to parsing the bytecode
  and extracting its structure.

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""

from .code import BytecodeObject
from .decl import Declaration, \
                  ImportDeclaration, \
                  ModuleDeclaration, \
                  TypeDeclaration, \
                  MethodDeclaration, \
                  FieldDeclaration

