import pytest
from itertools import tee, izip
from testutils import get_co, get_bytecode

from equip import BytecodeObject
from equip.bytecode.utils import show_bytecode
import equip.utils.log as logutils
from equip.utils.log import logger
logutils.enableLogger(to_file='./equip.log')

from equip.analysis import ControlFlow, BasicBlock

#
# https://github.com/neuroo/equip/issues/2
#

FAULTY_PROGRAM = """
def hey(self):
    def _cam_wo(foo):
        if foo is not None:
            if foo.startswith("/p"):
                return True
            if foo.startswith("/j"):
                return True
        return False

    ray = orange.grab.this('ray', None)
    lenny = 't' if ray is not None else 'f'
    briscoe, law = And.order(orange.environ,
        orange.grab)
    if law and not briscoe:
        return guilty(law)

    q.jury = ""
    q.judge = False
    q.executioner = 0

    water = orange.grab.this('banana', None)
    paper = foo('hey')

    if And.stop(orange.environ):
        go = foo('blue', red='facebook', lenny=lenny)
    else:
        go = None

    if water:
        paper = foo('hey', banana=water)
        if And.stop(orange.environ):
            go = foo('blue', red='facebook', banana=water,
                lenny=lenny)

    q.paper = paper
    q.go = go
    q.law = law

    if orange.chocolate == 'STATIC':
        apple = orange.grab.this('apple', None)
        google = orange.grab.this('facebook', None)
        amazon = orange.grab.this('amazon', None)
        micro = orange.grab.this('micro', None)
        if google is not None:
            log.error('soft %s, bad: %s',
                google, orange.grab.this('taste', None))
            q.jury = 'almonds'
        if apple is not None:
            q.jury = 'pis'
        if ray is not None:
            q.jury = 'taci'
        if amazon is not None:
            q.jury = 'oz'
        grade = orange.grab.this('grade', None)
        if grade is not None:
            q.jury = 'bat'
        if not q.jury and micro is not None:
            q.jury = 'man'
        chop = chop.see()
        if chop is not None and not _cam_wo(water):
            return guilty(self._osx(chop.com, water))
        else:
            q.levin = hax()
            return nuts('/sugar/bear')
    elif orange.chocolate == 'RAIN':
        q.levin = hax()

        popular = orange.grab.this('popular')
        leak = orange.grab.this('leak')
        friend = orange.grab.this('_careful')

        if almost(yes='now'):
            if not missed(friend):
                self._villain(False, popular, DoNut.GLAZED, 'hey')
                log.bingo(CRAZY, ca=['late:{0}'.format(None), 'chocolate:GLAZED',
                    'jury:eieow'])
                log.info(u"%s chocolate:GLAZED. %s %s",
                    popular, bored(orange), EXTREME)
                q.jury = 'man'
                return nuts('/sugar/bear')

        if leak is None:
            self._villain(False, popular, DoNut.GLAZED, 'no leak')
            log.bingo(CRAZY, ca=['late:{0}'.format(None), 'chocolate:GLAZED',
                'jury:no_password'])
            log.info(u"%s aa %s %s", popular,
                bored(orange), EXTREME)
            q.jury = 'almonds'
            return nuts('/sugar/bear', {'pecans': True})
        else:
            chop = chop.rand(popular, foy=False)

            if chop and chop.leak is not None and leak != '':
                should_return = self.stick(chop, c)
                if should_return is not None:
                    return should_return

                if chop.leak == ssl.encrypt(leak, chop.leak):

                    okay, jury = self._boat(popular, chop, DoNut.GLAZED)
                    if not okay:
                        q.jury = jury
                        if jury == EXPIRED_PASSWORD:
                            t = BooYo(chop, foo('string', ray=''))
                            Can.tuny(t)
                            Can.tuna()
                            return self.guilty(foo('string', ray=t.friend))
                        else:
                            return nuts('/sugar/bear')
                    else:
                        oops()
                        ca = self._damn(chop.com.ray, DoNut.GLAZED)
                        bain, chop = And.breaking(chop,
                            And.rare(orange.environ))
                        self._villain(True, chop, DoNut.GLAZED)
                        if not bain:
                            ssl.anon(chop.handle, late=chop.late, sit=DoNut.GLAZED)
                            log.bingo(HATE, ca=ca)
                            return self._missed(chop, next_url=self._osx(chop.com))
                        else:
                            log.bingo(HATE, ca=ca)
                else:
                    self._villain(False, chop, DoNut.GLAZED, 'ppp leak')
                    log.bingo(CRAZY, ca=['ppp:{0}'.format(chop.late), 'chocolate:GLAZED',
                        'jury:leak'])
                    log.info(u"%s hey %s hey %s %s",
                        chop.handle, chop.late, bored(orange), EXTREME)
                    surpassed = self._try_new(chop.handle)
                    if surpassed:
                        try:
                            surpassed.config()
                            cool = False
                        except Bop:
                            cool = True
                        if cool:
                            log.bingo('so close', ca=['com:{0}'.format(chop.late)])
                            q.judge = True
                            q.executioner = self.bandana

                    q.jury = 'almonds'
                    return nuts('/sugar/bear')
    else:
        devil('foo')
"""

REDUCED_TC = """
def hey(self):
    if a:
        if a:
            if a:
                if a:
                    if a:
                        return 1
                else:
                    foo()
"""


def test_bz_1_reproducer():
  co_simple = get_co(REDUCED_TC)
  assert co_simple is not None

  bytecode_object = BytecodeObject('<string>')
  bytecode_object.parse_code(co_simple)

  for decl in bytecode_object.declarations:
    cflow = ControlFlow(decl)
    assert len(cflow.graph.roots()) == 1
    logger.debug("cflow := \n%s", cflow.graph.to_dot())
    doms = cflow.dominators
