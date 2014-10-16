# -*- coding: utf-8 -*-
"""
  equip.rewriter.merger
  ~~~~~~~~~~~~~~~~~~~~~

  Responsible for merging two bytecodes at the specified places,
  as well as making sure the resulting bytecode (and code_object)
  is properly created.

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""
import opcode
import types
from dis import findlinestarts
from array import array

from ..utils.log import logger
from ..bytecode.code import BytecodeObject
from ..bytecode.utils import get_debug_code_object_dict, \
                             get_debug_code_object_info, \
                             show_bytecode, \
                             CO_FIELDS

PLACEHOLDER = -2
RETURN_VALUE = 83
LOAD_NAME = 101
LOAD_GLOBAL = 116
LOAD_FAST = 124
STORE_FAST = 125


#: This global name is always injected as a new variable in ``co_varnames``,
#: and used to carry the return values. We essentially add::
#:
#:   STORE_FAST '_______0x42024_retvalue'
#:   ... instrument code that can use `{return_value}`
#:   LOAD_FAST  '_______0x42024_retvalue'
#:   RETURN_VALUE
#:
#: as specified by the ``RETURN_INSTR_TEMPLATE``.
RETURN_CANARY_NAME = '_______0x42024_retvalue' # yeah...


#: The template that dictates how return values are being captured.
RETURN_INSTR_TEMPLATE = (
  (STORE_FAST, RETURN_CANARY_NAME),
  (PLACEHOLDER, None),             # <---- actual return instrumentation code
  (LOAD_FAST, RETURN_CANARY_NAME),
)


class CodeObject(object):
  """
    Class responsible for merging two code objects, and generating a new one.
    This effectively creates the new bytecode that will be executed.
  """

  def __init__(self, co_origin):
    if not isinstance(co_origin, types.CodeType):
      raise Exception('The creation of the `CodeObject` should get the original code_object')

    self.co_origin = co_origin
    self.fields = dict(zip(CO_FIELDS, [getattr(self.co_origin, f) for f in CO_FIELDS]))
    self.code = array('B')
    self.linestarts = dict(findlinestarts(co_origin))

    self.lnotab = array('B')
    self.append_code = self.code.append
    self.insert_code = self.code.insert
    self.prev_lineno = -1

    # Used for conversion from a LOAD_NAME in the probe code to a LOAD_FAST
    # in the final bytecode if the names are variable names (in co_varnames)
    self.name_to_fast = set()

    # Used for conversion from a LOAD_NAME in the probe code to a LOAD_GLOBAL
    # when the name is from an injected import
    self.name_to_global = set()


  def add_global_name(self, global_name):
    """
      Adds the ``global_name`` as a known imported name. The instrument bytecode
      will get modified to change any LOAD_* to a LOAD_GLOBAL when finding this
      name.

      :param global_name: The imported global name.
    """
    self.name_to_global.add(global_name)


  #: List of fields in the code_object not to merge. We only keep the ones from
  #: the original code_object.
  MERGE_BACKLIST = ('co_code', 'co_firstlineno', 'co_name', 'co_filename',
                    'co_lnotab', 'co_flags', 'co_argcount')


  def merge_fields(self, co_other):
    """
      Merges fields from the code_object. The only fields that aren't merged,
      are listed in `MERGE_BACKLIST`.

      :param co_other: The other code_object to merge the `co_origin` with.
    """
    for f in CO_FIELDS:
      if f in CodeObject.MERGE_BACKLIST:
        continue
      elif f == 'co_stacksize':
        # We don't recompute the required stacksize, but just get the max from
        # the two code_objects
        self.fields['co_stacksize'] = max(self.fields['co_stacksize'],
                                          getattr(co_other, f))
      elif f == 'co_nlocals':
        self.fields['co_nlocals'] = self.fields['co_nlocals'] \
                                  + getattr(co_other, f)      \
                                  + 1 # for the return value `RETURN_CANARY_NAME`
      elif f == 'co_names':
        for co_name in getattr(co_other, 'co_names'):
          if co_name not in self.fields['co_varnames']:
            self.fields['co_names'] = self.fields['co_names'] + (co_name,)
          else:
            # self.fields['co_varnames'] = self.fields['co_varnames'] + (co_name,)
            self.name_to_fast.add(co_name)
      else:
        # Should only be tuples
        tpl_other = getattr(co_other, f)
        # We need to keep the ordering, as it matters for the formal parameters
        # which are the first...
        for val in tpl_other:
          if val not in self.fields[f]:
            self.fields[f] = self.fields[f] + (val,)

        if f == 'co_varnames' and RETURN_CANARY_NAME not in self.fields[f]:
          self.fields[f] = self.fields[f] + (RETURN_CANARY_NAME,)


  def reset_code(self):
    self.code = array('B')
    self.lnotab = array('B')
    self.append_code = self.code.append
    self.insert_code = self.code.insert


  def append(self, op, arg, bc_index=-1, lineno=-1):
    self.insert(len(self.code) - 1 if len(self.code) else 0, op, arg, bc_index, lineno)


  def prepend(self, op, arg, bc_index=-1, lineno=-1):
    self.insert(0, op, arg, bc_index)


  # Convert the `arg` into the right insertion and an oparg to burn in the code
  def insert(self, index, op, arg, bc_index=-1, lineno=-1):
    op, oparg = self.get_op_oparg(op, arg, bc_index)
    self.emit(op, oparg, arg, lineno)


  def get_op_oparg(self, op, arg, bc_index=0):
    """
      Retrieve the opcode (`op`) and its argument (`oparg`) from the supplied
      opcode and argument.

      :param op: The current opcode.
      :param arg: The current dereferenced argument.
      :param bc_index: The current bytecode index.
    """

    # Conversion of LOAD_NAME opcode based on injected references (global, vars)
    if op == LOAD_NAME:
      if arg in self.name_to_fast:
        op = LOAD_FAST
      elif arg in self.name_to_global:
        op = LOAD_GLOBAL

    oparg = None
    if op >= opcode.HAVE_ARGUMENT:
      if op in opcode.hasconst:
        oparg = self.add_get_constant(arg)
      elif op in opcode.hasname:
        oparg = self.add_get_names(arg)
      elif op in opcode.haslocal:
        oparg = self.add_get_varnames(arg)
      elif op in opcode.hascompare:
        oparg = opcode.cmp_op.index(arg)
      elif op in opcode.hasfree:
        oparg = self.add_get_cellvars_freevars(arg)
      elif op in opcode.hasjrel or op in opcode.hasjabs:
        oparg = arg
      else:
        oparg = arg
    return op, oparg


  def emit(self, op, oparg, arg=None, lineno=-1):
    """
      Writes the bytecode and lnotab.
    """
    bytecode_inc, line_inc = 0, -1

    if op >= opcode.HAVE_ARGUMENT and oparg > 0xffff:
      self.append_code(opcode.EXTENDED_ARG)
      self.append_code((oparg >> 16) & 0xff)
      self.append_code((oparg >> 24) & 0xff)
      bytecode_inc += 3

    self.append_code(op)
    bytecode_inc += 1

    if op >= opcode.HAVE_ARGUMENT:
      self.append_code(oparg & 0xff)
      self.append_code((oparg >> 8) & 0xff)
      bytecode_inc += 2

    # We also adjust the lnotabs field
    if self.prev_lineno == -1:
      line_inc = 0
    else:
      line_inc = lineno - self.prev_lineno

    if line_inc == 0 and bytecode_inc == 0:
      self.lnotab.append(0)  # bytecode increment
      self.lnotab.append(0)  # lineno increment
    else:
      while bytecode_inc > 255:
        self.lnotab.append(255)
        self.lnotab.append(0)
        bytecode_inc -= 255

      while line_inc > 255:
        self.lnotab.append(0)
        self.lnotab.append(255)
        line_inc -= 255

      # Add the remainder
      self.lnotab.append(bytecode_inc)
      self.lnotab.append(line_inc)

    self.prev_lineno = lineno


  def get_instruction_size(self, op, arg=None, bc_index=0):
    op, oparg = self.get_op_oparg(op, arg, bc_index)
    if op < opcode.HAVE_ARGUMENT:
      return 1
    if oparg > 0xffff:
      return 5
    return 3


  JUMP_OP = opcode.hasjrel + opcode.hasjabs

  @staticmethod
  def is_jump_op(op):
    return op in CodeObject.JUMP_OP


  def add_get_constant(self, const):
    return self.add_get_tuple(const, 'co_consts')


  def add_get_names(self, name):
    return self.add_get_tuple(name, 'co_names')


  def add_get_varnames(self, const):
    return self.add_get_tuple(const, 'co_varnames')


  def add_get_cellvars_freevars(self, varname):
    if varname in self.fields['co_cellvars']:
      return self.fields['co_cellvars'].index(varname)
    elif varname in self.fields['co_freevars']:
      return self.fields['co_freevars'].index(varname)
    else:
      return self.add_get_tuple(varname, 'co_freevars')

  # This is now just a getter since all fields have been merged already
  def add_get_tuple(self, value, field_name):
    return self.fields[field_name].index(value)


  # Create a new code_object with the info from this class
  def to_code(self):
    return types.CodeType(self.fields['co_argcount'], self.fields['co_nlocals'],
                          self.fields['co_stacksize'], self.fields['co_flags'],
                          self.code.tostring(), self.fields['co_consts'],
                          self.fields['co_names'], self.fields['co_varnames'],
                          self.fields['co_filename'], self.fields['co_name'],
                          self.fields['co_firstlineno'], self.lnotab.tostring(),
                          self.fields['co_freevars'], self.fields['co_cellvars'])


class Merger(object):
  #: Error case for the kind of location for the merge.
  UNKNOWN = 0

  #: Only valid for ``MethodDeclaration``. This specifies that the instrument
  #: code should be injected before the body.
  BEFORE = 1

  #: Only valid for ``MethodDeclaration``. This specifies that the instrument
  #: code should be injected before each return of the method (i.e., before
  #: each encountered ``RETURN_VALUE`` in the bytecode).
  AFTER = 2

  #: Valid for all ``Declaration``. This specifies that the instrument code
  #: should be injected each time the current line number changes.
  LINENO = 3

  #: Valid for all ``Declaration``. This specifies that the instrument code
  #: should be injected after each instrument.
  INSTRUCTION = 4

  #: Valid for ``ModuleDeclaration`` or ``MethodDeclaration``. This specifies that
  #: the instrument code should be injected before the encountered imports.
  BEFORE_IMPORTS = 5

  #: Valid for ``ModuleDeclaration`` or ``MethodDeclaration``. This specifies that
  #: the instrument code should be injected after the encountered imports.
  AFTER_IMPORTS = 6

  #: Unused.
  RETURN_VALUES = 7

  #: Valid for ``ModuleDeclaration``. This specifies that the code should be injected
  #: at the beginning of the module.
  MODULE_ENTER = 8

  #: Valid for ``ModuleDeclaration``. This specifies that the code should be injected
  #: at the end of the module.
  MODULE_EXIT = 9


  @staticmethod
  def merge(co_source, co_input, location=UNKNOWN, \
            ins_lineno=-1, ins_offset=-1, ins_import_names=None):
    """
      The merger makes sure that the bytecode is properly inserted where
      it should be, but also that the consts/names/locals/etc. are re-indexed.
      We will always append at the end of the current tuples.

      We need to first compute the new bytecode resolve the jumps, and then dump it...
      if we just emit it as right now, we have an issue since we cannot know where an
      absolute/relative jump will land since some instr code can be inserted in between.
    """
    if not co_input:
      raise Exception('Input code_object is None')

    new_co = CodeObject(co_source)
    new_co.merge_fields(co_input)
    new_co.reset_code()

    bc_source = BytecodeObject.get_parsed_code(co_source)
    bc_input = BytecodeObject.get_parsed_code(co_input)[:-2]

    # logger.debug("ins_import_names := %s", ins_import_names)

    if ins_import_names:
      for name in ins_import_names:
        # logger.debug("Adding global name: %s", name)
        new_co.add_global_name(name)

    # logger.debug("Enter code_object:\n" + get_debug_code_object_info(co_input))
    # logger.debug("Instrument bytecode:\n%s", show_bytecode(bc_input))

    new_bytecode = None
    if location == Merger.MODULE_EXIT:
      new_bytecode = Merger.merge_exit(new_co, bc_source, bc_input, ins_import_names)
    else:

      if Merger.already_instrumented(bc_source, bc_input):
        logger.debug("Already instrumented code object. Skipping")
        return

      # list [(bc elements), instrument_code frame counter)]
      bytecode = Merger.get_final_bytecode(bc_source, bc_input,
                                           co_source, co_input,
                                           location,
                                           ins_lineno, ins_offset)

      new_bytecode = Merger.resolve_jump_targets(bytecode, new_co)

    for bc_tpl in new_bytecode:
      new_co.append(bc_tpl[0][2], bc_tpl[0][3], bc_tpl[0][0], bc_tpl[0][1])

    final_new_co = new_co.to_code()

    # logger.debug("New code_object:\n" + get_debug_code_object_info(final_new_co))
    # final_bc = BytecodeObject.get_parsed_code(final_new_co)
    # logger.debug("New bytecode:\n" + show_bytecode(final_bc))

    return final_new_co


  @staticmethod
  def merge_exit(new_co, bc_source, bc_input, ins_import_names=None):
    """
      Special handler for inserting code at the very end of a module.
    """
    length = len(bc_source)
    input_length = len(bc_input)
    end_index = length - 2
    co_source = bc_source[0][5]

    unrolled_bytecode = []
    j, injection_start = 0, 0
    i = 0
    while i < length:
      current_index, lineno, op, arg, cflow_in, code_object = bc_source[i]
      if code_object != co_source:
        i += 1
        continue

      if i == end_index:
        injection_start = j
        Merger.inline_instrument(unrolled_bytecode, bc_input, lineno, -1)

      unrolled_bytecode.append(((current_index, lineno, op, arg, cflow_in, code_object), -1))
      j += 1
      i += 1

    # Fix ending jump targets by making them absolute
    bc_indices = Merger.build_bytecode_offsets(new_co, unrolled_bytecode)

    new_bytecode = []
    i = 0
    length = len(unrolled_bytecode)

    while i < length:
      bc_tpl = unrolled_bytecode[i]
      op, arg, index, instr = bc_tpl[0][2], bc_tpl[0][3], bc_tpl[0][0], bc_tpl[1]
      if CodeObject.is_jump_op(op) and i >= injection_start and i < (injection_start + input_length):
        new_address = arg
        # We actually need to change the addresses form the exit code
        if op in opcode.hasjabs:
          new_address = (arg - index) + bc_indices[i]
        else:
          new_address = arg

        new_bytecode.append(((bc_indices[i], bc_tpl[0][1], bc_tpl[0][2], \
                              new_address, bc_tpl[0][4], bc_tpl[0][5]), \
                             instr))
      else:
        new_bytecode.append(((bc_indices[i], bc_tpl[0][1], bc_tpl[0][2], \
                              bc_tpl[0][3], bc_tpl[0][4], bc_tpl[0][5]), \
                             instr))
      i += 1

    return new_bytecode


  @staticmethod
  def already_instrumented(bc_source, bc_input):
    """
      Checks if the instrumentation in bc_input is already in bc_source
    """
    op_arg_source = [(tpl[2], tpl[3]) for tpl in bc_source if tpl[2] not in opcode.hasjabs]
    op_arg_input = [(tpl[2], tpl[3]) for tpl in bc_input if tpl[2] not in opcode.hasjabs]

    source_length, input_length = len(op_arg_source), len(op_arg_input)
    if source_length <= input_length:
      return False
    for i in xrange(source_length):
      if op_arg_input == op_arg_source[i:i + input_length]:
        return True
    return False


  @staticmethod
  def build_bytecode_offsets(new_co, bytecode):
    bc_indices = []
    current_size = 0
    for bc_tpl in bytecode:
      bc_indices.append(current_size)
      current_size += new_co.get_instruction_size(op=bc_tpl[0][2],
                                                  arg=bc_tpl[0][3],
                                                  bc_index=bc_tpl[0][0])
    return bc_indices


  @staticmethod
  def resolve_jump_targets(bytecode, new_co):
    """
      Resolves targets of jumps. Since we add new bytecode, absolute (resp. relative)
      jump address (resp. offset) can change and we need to track the changes to find
      the new targets.

      The resolver works in two phases:

      1. Create the list of bytecode indices based on the size of the
         opcode and its argument.
      2. For each jump opcode, take its argument and resolve it in the same
         part of the bytecode (e.g., instrument bytecode or original bytecode).

      :param bytecode: The structure computed by ``get_final_bytecode`` which overlays
                       the final bytecode sequences and its origin.
      :param new_co: The currently created ``CodeObject``.
    """
    new_bytecode = []
    bc_indices = Merger.build_bytecode_offsets(new_co, bytecode)
    length = len(bc_indices)

    def find_target_index(target, j, instr_counter, current_index, op):
      direction = 1
      is_absolute = False
      if op in opcode.hasjabs:
        direction = 1 if target > current_index else -1
        is_absolute = True
      else:
        direction = 1 if target >= 0 else -1
      bound = -1 if direction < 0 else length

      # Search in the same instrumentation code if the target address is
      # already present. If so, we just return that one.
      k = j
      while k != bound:
        if bytecode[k][0][0] == target and bytecode[k][1] == instr_counter:
          return k
        k += direction

      # If we didn't find a match for the jump, we need to look outside of the
      # bounds of the same source code.
      k = j
      current_pos = bc_indices[j]
      increment = (bytecode[j][0][3] - bytecode[j][0][0]) if is_absolute else (bytecode[j][0][3] + 3)
      idx = bc_indices.index(current_pos + increment)
      return idx


    i = 0
    for bc_tpl in bytecode:
      op, arg, index, instr = bc_tpl[0][2], bc_tpl[0][3], bc_tpl[0][0], bc_tpl[1]
      if not CodeObject.is_jump_op(op):
        new_bytecode.append(((bc_indices[i], bc_tpl[0][1], bc_tpl[0][2], \
                              bc_tpl[0][3], bc_tpl[0][4], bc_tpl[0][5]), \
                             instr))
      else:
        new_address = -1
        target_address = arg if op in opcode.hasjabs else (index + 3 + arg)
        target_index = find_target_index(target_address, i, instr, index, op)

        if op in opcode.hasjrel:
          new_address = bc_indices[target_index] - bc_indices[i] - 3
        else:
          new_address = bc_indices[target_index]

        new_bytecode.append(((bc_indices[i], bc_tpl[0][1], bc_tpl[0][2], \
                              new_address, bc_tpl[0][4], bc_tpl[0][5]), \
                             instr))
      i += 1

    return new_bytecode


  @staticmethod
  def get_final_bytecode(bc_source, bc_input, co_source, co_input, \
                         location, ins_lineno, ins_offset=-1):
    """
      Computes the final sequences of opcodes and keep old values. It also tracks
      what sequences come from the instrument code or the original code, so we can
      resolve jumps.

      :param bc_source: The bytecode of the orignal code.
      :param bc_input: The instrument bytecode to inject.
      :param co_source: The orignal code object.
      :param co_input: The instrument code object.
      :param location: The location of the instrumentation. It should be either: ``BEFORE``,
                       ``AFTER``, ``LINENO``, etc.
      :param ins_lineno: The line number to inject the instrument at. Only valid when
                         the injection location is ``LINENO``.
      :param ins_offset: Not used.
    """
    bytecode = []
    instr_counter = 0

    i, length = 0, len(bc_source)
    current_index, lineno = -1, -1
    while i < length:
      current_index, lineno, op, arg, cflow_in, code_object = bc_source[i]
      if code_object != co_source:
        i += 1
        continue

      if location in (Merger.BEFORE, Merger.MODULE_ENTER) and i == 0:
        instr_counter += 1
        Merger.inline_instrument(bytecode, bc_input, lineno, instr_counter,
                                 location=location)

      elif location == Merger.LINENO and lineno == ins_lineno:
        instr_counter += 1
        Merger.inline_instrument(bytecode, bc_input, lineno, instr_counter,
                                 location=location)

      elif location == Merger.AFTER and op == RETURN_VALUE:
        instr_counter += 1
        Merger.inline_instrument(bytecode, bc_input, lineno, instr_counter,
                                 template=RETURN_INSTR_TEMPLATE, location=location)

      # Append current code
      bytecode.append(((current_index, lineno, op, arg, cflow_in, code_object), -1))

      if location == Merger.INSTRUCTION:
        instr_counter += 1
        Merger.inline_instrument(bytecode, bc_input, lineno, instr_counter,
                                 location=location)

      if location == Merger.MODULE_EXIT and i == length - 3:
        instr_counter += 1
        Merger.inline_instrument(bytecode, bc_input, lineno, -1,
                                 location=location)
      i += 1

    return bytecode


  @staticmethod
  def inline_instrument(dst_bytecode, src_bytecode, original_lineno, \
                        instr_counter=-1, template=None, location=UNKNOWN):
    """
      Inline the instrument bytecode in place of the current state of ``dst_bytecode``.

      :param dst_bytecode: The list that contains the final bytecode.
      :param src_bytecode: The bytecode of the instrument.
      :param original_lineno: The line number from the original bytecode, so we always
                              map the instrument code line numbers to the code being
                              instrumented.
      :param instr_counter: A counter to track the frames of the different instrumentation
                            code being inlined. This is used to resolve jump targets.
      :param template: An instrumentation can follow a template, if so, the actual
                       template is supplied here. An example is the instrumentation ``AFTER``
                       which requires to capture the return value. Defaults to None.
    """
    template_idx, template_length = 0, 0
    b_current_index, b_lineno, b_op, b_arg, b_cflow_in, b_code_object = src_bytecode[0]

    if template is not None:
      template_length = len(template)
      # Unroll the template until we reached PLACEHOLDER
      while template_idx < template_length:
        t_op, t_arg = template[template_idx]
        if t_op == PLACEHOLDER:
          break
        dst_bytecode.append(((b_current_index, original_lineno, t_op, t_arg,
                              b_cflow_in, b_code_object),
                             instr_counter))
        template_idx += 1

    # Inline the entire instrument code
    bc_i, bc_length = 0, len(src_bytecode)
    while bc_i < bc_length:
      b_current_index, b_lineno, b_op, b_arg, b_cflow_in, b_code_object = src_bytecode[bc_i]
      if b_op != RETURN_VALUE:
        dst_bytecode.append(((b_current_index, original_lineno, b_op, b_arg,
                              b_cflow_in, b_code_object),
                             instr_counter))
      bc_i += 1

    if template is not None:
      template_idx += 1
      while template_idx < template_length:
        t_op, t_arg = template[template_idx]
        dst_bytecode.append(((b_current_index, original_lineno, t_op, t_arg,
                              b_cflow_in, b_code_object),
                             instr_counter))
        template_idx += 1

