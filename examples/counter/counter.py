import json
import os

DEFAULT_JSON_OUTPUT = 'global-counter.json'

# Simple structure to capture counts for module/method
# in the instrumented program.
class GlobalCounter:
  def __init__(self):
    self.data = {}

  @staticmethod
  def fqn(class_name, method, lineno):
    name = method + ':' + str(lineno)
    if class_name and class_name != 'None':
      name = class_name + '::' + name
    return name

  def count(self, file, class_name=None, method=None, lineno=-1):
    if file not in self.data:
      self.data[file] = {}
    d = self.data[file]
    name = GlobalCounter.fqn(class_name, method, lineno)

    if name not in d:
      d[name] = 0
    d[name] += 1

  def to_json(self, file_location=DEFAULT_JSON_OUTPUT):
    print "Writing to %s" %  file_location
    try:
      fd = open(file_location, 'w')
      json.dump(self.data, fd, indent=2, sort_keys=True)
      fd.close()
    except Exception, ex:
      print "Serialization error:", str(ex)


GlobalCounterInst = GlobalCounter()
