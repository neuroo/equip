# -*- coding: utf-8 -*-
"""
  equip.analysis.dataflow
  ~~~~~~~~~~~~~~~~~~~~~~~

  Different kind of data flow analyzes.

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""

from .fixedpoint import Dataflow,        \
                        ForwardDataflow, \
                        BackwardDataflow
from .lattice import Lattice
from .state import States,  \
                   State,   \
                   Transfer
