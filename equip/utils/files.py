# -*- coding: utf-8 -*-
"""
  equip.utils.files
  ~~~~~~~~~~~~~~~~~

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""
import os

__normalize_path = lambda x: os.path.abspath(x)


def file_extension(filename):
  if '.' not in filename:
    return None
  return filename[filename.rfind('.') + 1:].lower()


def good_ext(fext, l=None):
  return fext.lower() in l if l else False


def scan_dir(directory, files, l_ext=None):
  names = os.listdir(directory)
  for name in names:
    srcname = __normalize_path(os.path.join(directory, name))
    try:
      if os.path.isdir(srcname):
        try:
          scan_dir(srcname, files, l_ext)
        except:
          continue
      elif os.path.isfile(srcname) \
           and (not l_ext \
                or good_ext(srcname[srcname.rfind('.')+1:], l_ext)):
        if srcname not in files:
          files.append(srcname)
    except IOError, error:
      continue


def list_dir(directory):
  subdirs = os.listdir(directory)
  if not subdirs:
    return []
  return [os.path.join(directory, k) for k in subdirs]
