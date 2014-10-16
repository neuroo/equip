import equip

def get_co(code):
  return compile(code, '<string>', 'exec')

def get_bytecode(co):
  return equip.BytecodeObject.get_parsed_code(co)
