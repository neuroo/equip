# -*- coding: utf-8 -*-
"""
  equip.prog
  ~~~~~~~~~~

  Handles the current program for instrumentation.

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""
import os
import compileall

from .utils.log import logger
from .utils.files import scan_dir


class Program(object):
  """
    Captures the sources and binaries from the current program to instrument.
  """
  def __init__(self, instrumentation):
    self.instrumentation = instrumentation
    self.options = self.instrumentation.options
    self.input_location = self.instrumentation.location
    self.program_files = []
    self._bytecode_files = []

    if isinstance(self.input_location, basestring):
      self.input_location = (self.input_location,)


  def create_program(self, skip_rebuild=False):
    """
      Creates the structure of the program with its source files and
      binary files. When the ``Instrument`` option ``force-rebuild``
      is set, it will trigger the compilation of all python source files.

      :param skip_rebuild: Force skipping the build. Mostly here due to the
                           recursive nature of this function.
    """
    self.program_files = []
    self._bytecode_files = []
    for location in self.input_location:
      scan_dir(location, self.program_files, ('py', 'pyc'))

    # Do we need to compile all the files?
    py_files, pyc_files = Program.split_program_source_bc(self.program_files)

    logger.debug("Force rebuilding? %s", self.options.get('force-rebuild'))

    if not skip_rebuild:
      if len(py_files) != len(pyc_files) or self.instrumentation.get_option('force-rebuild'):
        self.compile_program()
    else:
      self._bytecode_files = list(pyc_files)
      logger.debug("Bytecode := %s", pyc_files)


  def compile_program(self):
    """
      Compiles the program.
    """
    for location in self.input_location:
      compileall.compile_dir(location, quiet=True)
    self.create_program(skip_rebuild=True)


  @property
  def bytecode_files(self):
    """
      The list of pyc files.
    """
    if not self._bytecode_files:
      self.create_program()
    return self._bytecode_files


  @staticmethod
  def split_program_source_bc(lst):
    py_files, pyc_files = [], []
    for f in lst:
      dest = py_files if f.lower().endswith('.py') else pyc_files
      dest.append(f)
    return py_files, pyc_files


