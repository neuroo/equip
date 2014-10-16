# -*- coding: utf-8 -*-
"""
  equip.utils.log
  ~~~~~~~~~~~~~~~

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""
import logging


LOGGING_FMT = '%(asctime)s - %(levelname)3s] %(filename)s::%(funcName)s(%(lineno)d) - %(message)s'


def removeOtherHandlers(to_keep=None):
  for hdl in logger.handlers:
    if hdl != to_keep:
      logger.removeHandler(hdl)


def enableLogger(to_file=None):
  logger.setLevel(logging.DEBUG)
  ch = logging.StreamHandler() if not to_file else logging.FileHandler(to_file, mode='w')
  ch.setLevel(logging.DEBUG)
  fmt = logging.Formatter(LOGGING_FMT)
  ch.setFormatter(fmt)
  logger.addHandler(ch)
  removeOtherHandlers(ch)

# logging.basicConfig(level=logging.DEBUG, handler=logging.NullHandler)
logger = logging.getLogger('equip')
removeOtherHandlers()

