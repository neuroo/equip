# -*- coding: utf-8 -*-
"""
  equip.analysis.dataflow.utils
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  A set of common operators.

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""
import copy

# { key -> set() }
def dict_union(dct1, dct2):
  result = copy.deepcopy(dct1)
  for key in dct2:
    result[key] = dct2[key] if key not in result else result[key].union(dct2[key])
  return result
