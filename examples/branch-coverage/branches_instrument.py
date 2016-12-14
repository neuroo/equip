# -*- coding: utf-8 -*-
"""
  Branch Coverage Instrumentation
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""
import sys
from equip import Program, \
                  Instrumentation, \
                  SimpleRewriter, \
                  MethodVisitor
import equip.utils.log as logutils
from equip.utils.log import logger
logutils.enableLogger(to_file='./equip.log')






def main(argc, argv):
  if argc < 2:
    print HELP_MESSAGE
    return

  instr = Instrumentation(argv[1])
  instr.set_option('force-rebuild')

  if not instr.prepare_program():
    print "[ERROR] Cannot find program code to instrument"
    return



if __name__ == '__main__':
  main(len(sys.argv), sys.argv)
