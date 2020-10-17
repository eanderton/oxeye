# -*- coding: utf-8 -*-
'''
Matching functions for parse rules.
'''

import re


def failed_match():
    '''
    Returns a match tuple for a failed result.
    '''

    return (False, 0, (), {})


def passed_match(advance, args=(), kwargs={}):
    '''
    Returns a match tuple for a successful result.  The args and kwargs are
    intended for forwarding to an associated predicate function.
    '''

    return (True, advance, args, kwargs)


def match_any(sequence):
    '''
    Matches any head element on sequence.
    '''

    if len(sequence) == 0:
        return failed_match()
    return passed_match(1, (sequence[0],))


def match_peek(sequence):
    '''
    Matches any head element, but does not advance the parser.  May be used in
    conjunction with `nop` to move the parser to a different state.
    '''

    if len(sequence) == 0:
        return failed_match()
    return passed_match(0, (sequence[0],))


def match_set(value_set):
    '''
    Matches if a token matches any one value in `value_set`, by using the `in`
    operator.  The `value_set` may be any object that implements `__in__`.
    '''

    def impl(sequence):
        if len(sequence) == 0:
            return failed_match()
        head = sequence[0]
        if head in value_set:
            return passed_match(1, (head,))
        return failed_match()
    return impl


def match_all(sequence):
    '''
    Matches against the entire sequence and passes it to the predicate.
    May also be used in conjunction with `nop` to exhaust the parser.
    '''

    if len(sequence) == 0:
        return failed_match()
    return passed_match(len(sequence), (sequence,))


def match_head(value):
    '''
    Match function that matches a value against the head of the sequence.
    '''

    def impl(sequence):
        if len(sequence) == 0:
            return failed_match()
        head = sequence[0]
        if head == value:
            return passed_match(1, (head,))
        return failed_match()
    return impl


def match_seq(values):
    '''
    Returns a match function that matches `values` against the multiple succesive
    elements from the head of the sequence.
    '''

    values_len = len(values)
    def impl(sequence):
        if len(sequence) < values_len:
            return failed_match()
        sub_sequence = sequence[:values_len]
        if sub_sequence == values:
            return passed_match(values_len, (sub_sequence,))
        return failed_match()
    return impl


def match_rex(expr):
    '''
    Match function that matches a regular expression against multiple character
    tokens.  The resulting groups and groupdict are passed to the predicate
    as *args and **kwargs, respectively, if there's a match.

    NOTE: will only work with sequeneces of type 'str', as the entire
    sequence is passed directly to a compiled regex type (see `re` library).
    '''

    rex = re.compile(expr)
    def impl(sequence):
        result = rex.match(sequence)
        if result:
            return passed_match(result.end(), result.groups(), result.groupdict())
        return failed_match()
    return impl


def match_end():
    '''
    Match the end of the grammar.

    Used to write closed grammars that may run with exhaustive=True.
    '''
    def impl(sequence):
        return len(sequence) == 0
    return impl
