# -*- coding: utf-8 -*-
'''
Standard rules for building grammars.
'''

from oxeye.exception import ParseError


def failed_rule():
    '''
    Returns a rule tuple for a failed rule match.
    '''

    return (False, 0, None)


def passed_rule(advance, next_state):
    '''
    Returns a rule tuple for a successful rule match.  The advance argument
    instructs the parser to advance by as many tokens, as though they were
    consumed by the operation.  The next_state insructs the parser to
    match the next token on the given state.
    '''

    return (True, advance, next_state)


def rule_next(state):
    '''
    Returns a rule function that advances the parser to the next state
    '''

    def impl(sequence):
        return passed_rule(0, state)
    return impl


def rule_fail(message):
    '''
    Returns a rule function that throws a ParseError with the provided message.
    '''

    def impl(sequence):
        raise ParseError(message)
    return impl


def rule_end(sequence):
    '''
    Distinct state that signals the end of the grammar.  Matches only on the
    very end of the parsed sequence.
    '''

    if len(sequence) == 0:
        return passed_rule(0, None)
    return failed_rule()
