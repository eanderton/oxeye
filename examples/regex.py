# -*- coding: utf-8 -*-
'''
Regular expression evaluator example.

While not as performant as the built-in regular expression
implementation, this example shows how to build a reasonably
complex grammar such as regular expressions.

NOTE: This example is not intended to be used as a viable
replacement for the `re` library.
'''

from __future__ import unicode_literals, absolute_import

from oxeye.parser import Parser, ParseError
from oxeye.match import match_any, match_seq
from oxeye.pred import nop
from oxeye.rule import rule_fail, rule_end, rule_next, rule_branch
from functools import partial

# NFA implementation: https://swtch.com/~rsc/regexp/regexp1.html

class RegexImpl(Parser):
    pass

'''
foo|bar

p = pass1
f = fail1
s = f
s = fo
s = foo
OR
  - set sequence fail to curent
  - push sequence
s = b
s = ba
s = bar
pop sequence

-----------
goal:
    start_group 0
    f 002 fail001
002:
    o 003 fail001
003:
    o pass001 004
004:
    start_group(0)
    b 004 fail001
005:
    a 006 fail001
006:
    r pass001 fail001

pass001:
    end_group(0)

fail001:
    nop

each sequence needs to be fixed up after it is concluded
'''

class Fragment(object):
    def __init__(self, name, *states):
        self.states = states
        self.name = name
        self.pass_state = 'pass'
        self.fail_state = 'fail'

    def __str__(self):
        return ','.join(
            ['({}, {}, {})'.format(x, self.pass_state, self.fail_state) for x in self.states]
        )


class RegularExpression(Parser):
    '''
    Regular expression compiler and interface.
    '''

    def _frag(self, *states):
        name = self._id
        self._operands.append(Fragment(name, *states))
        self._id = self._id + 1

    def op_eol(self):
        self._end_lit_sequence()
        self._frag('END')

    def op_sol(self):
        self._end_lit_sequence()
        self._frag('START')

    def op_or(self):
        b = self._operands.pop()
        a = self._operands.pop()
        # fixup a.fail -> b.start
        a.fail_state = b.name
        self._operands.append((a, b))

    def _end_lit_sequence(self):
        if len(self._lit_sequence):
            self._frag(self._lit_sequence)
            self._lit_sequence = ""

    def _literal(self, lit):
        self._lit_sequence += lit

    def _do(self, op):
        def impl(tok):
            self._end_lit_sequence()
            self._operations.append(op)
        return impl

    def __init__(self):
        super(RegularExpression, self).__init__({
            'goal': (
                {
                    #'[': (self. char_class_start, 'char_class'),
                    #'(': (self.start_group, 'goal'),
                    #')': (self.end_group, 'goal'),
                    #'.': (self.store_any, 'goal'),
                    #'$': (self.store_eol, 'goal'),
                    #'^': (self.store_sol, 'goal'),
                    #'*': (self.zero_or_more, 'goal'),
                    #'+': (self.one_or_more, 'goal'),
                    '|': (self._do(self.op_or), 'goal'),
                    '\r': (self._literal, 'goal'),
                    '\n': (self._literal, 'goal'),
                    '\v': (self._literal, 'goal'),
                    '\t': (self._literal, 'goal'),
                    '\\': (nop, 'self.char_escape'),
                },
                (match_any, self._literal, 'goal'),
                rule_end,
            ),
            'char_escape': (
                {
                    'r': (partial(self._literal, '\r'), 'goal'),
                    'n': (partial(self._literal, '\n'), 'goal'),
                    'v': (partial(self._literal, '\v'), 'goal'),
                    't': (partial(self._literal, '\t'), 'goal'),
                },
                (match_any, self._literal, 'goal'),
            ),
            #'char_class': (
            #    ('^', self.char_class_negate, 'char_class_char'),
            #    rule_next('char_class_char'),
            #),
            #'char_class_char': (
            #    {
            #        ']': (self.char_class_end, 'goal'),
            #    },
            #    (match_any, self._literal, 'goal'),
            #),
        })

    def compile(self, expr):
        self._id = 0
        self._operations = []
        self._lit_sequence = ""
        self._operands = []
        self.parse(expr)
        self._end_lit_sequence()

    def compile2(self):
        for op in self._operations:
           op()

        self.reverse = {}
        self.nfa = {}
        self.state_number = 0
        self.current_state = {}
