# -*- coding: utf-8 -*-
'''
This mini-implementation of Oxeye is provided as a starting point
for implementing state-machine based grammars using a similar
approach.  The implementation itself is small enough to be easily
vendored (cut-and-paste) into another program, which may be
desireable over an entire module install and import.

If `oxeye.mini.parse` is too limiting, please see
`oxeye.parser.Parser` for a more feature-rich approach to this
style of state machine.

>>> text = """
... Not comment text
... # hello
... # commented
... Also not comment text
... # world
... """
>>> nop = lambda: None
>>> comments = []
>>> parse({
...     'goal': (
...         ('#\\s+(.*)\\n', comments.append, 'goal'),
...         ('.*\\n', nop, 'goal'),
...     ),
... }, text)
('goal', 68)

>>> print(comments)
['hello', 'commented', 'world']

'''

import re


def parse(spec, text, state='goal', pos=0):
    '''
    This function processes `text` against `spec` state-machine
    specification, starting at the specified `state` and optional `pos`
    in text.

    The parser runs to exhaustion, or when no more states can be
    matched.  Upon exhausting `test`, a status `(state, pos)` tuple
    for the current state and position is returned.

    The spec is a dictionary of state to rule list mappings, where each
    rule is a `(regular_expression, predicate_function, next_state_)`,
    tuple.

    When a regular expression is matched, the match groups are passed
    as `*args`, and the named matches as `**kwargs`, to the predicate
    function.

    See `oxeye.pred` for predicate function examples to use with this
    parser.
    '''
    while pos < len(text):
        for rex, fn, next_state in spec[state]:
            result = re.match(rex, text[pos:])
            if result:
                fn(*result.groups(), **result.groupdict())
                pos += result.end()
                state = next_state
                break
        else:
            break
    return state, pos
