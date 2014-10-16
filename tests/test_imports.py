import pytest
from testutils import get_co, get_bytecode

import equip
from equip.bytecode.utils import show_bytecode


IMPORTS_CODE = """
from __future__ import absolute_import
from .test_import import *
import sub
from . import sub
from .... import sub
import foo.bar
from foo import bar
import foo.bar as bar
from . import foo
import foo
from .. import bar
import bar
from ... import bar
from .... import bar
from foo import bar as baz
from foo import bar, baz, fooz
from foo import bar as bar1, baz as baz1, fooz as fooz1
from godot import didi, gogo
"""

def test_imports():
  co_imports = get_co(IMPORTS_CODE)
  import_bc = get_bytecode(co_imports)

  assert co_imports is not None
  assert len(import_bc) > 0

  import_stmts = equip.BytecodeObject.get_imports_from_bytecode(co_imports, import_bc)

  assert len(import_stmts) == 18

  splitted_imports = filter(lambda imp: imp != '', IMPORTS_CODE.split('\n'))

  i = 0
  for stmt in import_stmts:
    candidate_import = splitted_imports[i]
    stmt_str = repr(stmt)
    assert candidate_import in stmt_str
    i += 1


IMPORT_AS = "import foo as foo" # same as `import foo`

def test_import_as():
  co_imports = get_co(IMPORT_AS)
  import_bc = get_bytecode(co_imports)
  import_stmts = equip.BytecodeObject.get_imports_from_bytecode(co_imports, import_bc)
  assert len(import_stmts) == 1

  import_stmt = import_stmts[0]

  assert import_stmt.root == None
  assert import_stmt.aliases == [('foo', None)]

