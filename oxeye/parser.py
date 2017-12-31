# -*- coding: utf-8 -*-
'''
Oxeye Parser library.  Provides utility classes and functions for constructing
discrete state machines for parsing text or a token stream.
'''

from __future__ import unicode_literals, absolute_import

import re
from oxeye.multimethods import enable_descriptor_interface, singledispatch
from oxeye.multimethods_ext import Callable, patch_multimethod_clone


enable_descriptor_interface()
patch_multimethod_clone()


def nop(*args, **kwargs):
    '''
    Predicate function that does nothing. Intended for do-nothing terminals in a DFA spec.
    '''
    pass 


def err(msg):
    '''
    Predicate function that emits an exception for `msg`.
    '''
    def impl(*args, **kwargs):
        raise Exception(msg)
    return impl



class ParseError(Exception):
    '''
    Base error type for parse related errors.  May optionally include a nested
    exception if another exception was the cause for the error.

    See the parser `status` property for additional error context.
    '''
    pass


class CompileError(Exception):
    '''
    Error type for compilation-based errors.
    
    See the parser `status` property for additional error context.
    '''
    pass


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


class Parser(object):
    '''
    Core parser class.  Implements a token based parser based on a provided parser
    specification (`spec`).  The parser operates on an input set of tokens, that 
    may be any indexable type, including `str` or `unicode`.

    '''

    def __init__(self, spec, start_state='goal'):
        '''
        Parser constructor.  Builds a parser around the `spec` state machine that 
        is a dictionary of state to rule-set mappings.  An optional `start_state`
        may be specified if 'goal' isn't a valid state in the provided spec.

        The parser specification is compiled into a series of closure functions by
        way of type-matching   Tuples, Dicts, and callables are valid 
        rule types, each with their own special use cases and idioms.  The set of 
        supported dispatch types may be expanded by augmenting or extending these
        multimethods.

        See the module documentation for more information on rules.
        '''

        self.spec = {}
        self._start_state = start_state
        for self._state, tests in spec.iteritems():
            self.spec[self._state] = []
            for self._rule in range(len(tests)):
                rule = self._compile_rule(tests[self._rule])
                if not callable(rule):
                    raise CompileError('Rule must compile to a callable object')
                self.spec[self._state].append(rule)
        # TODO: semantic checking of next_state validity
        self.reset()


    @singledispatch
    def _compile_rule(self, rule):
        '''
        Default dispatch function for compiling rules.  Raises an exception as
        no other dispatchable types were matched.
        '''

        raise CompileError('No registered method to compile rule', rule)

    @_compile_rule.method(Callable)
    def _compile_callable_rule(self, rule):
        '''
        compiler dispatch function for callable rules.  Callables are allowed
        to simply pass-through to the compiled output.
        '''
        return rule
        

    @_compile_rule.method(list)
    @_compile_rule.method(tuple)
    def _compile_tuple_rule(self, rule):
        '''
        Compiler dispatch function for tuple-based rules.  Returns a function
        that processes zero or more tokens, and returns a passed/failed rule 
        tuple as a result.
        '''

        match_tok, predicate_fn, next_state = rule
        match_fn = self._compile_match(match_tok)
        if not callable(match_fn):
            raise CompileError('Rule match function must compile to a callable object')
        def impl(tokens):
            match_success, advance, predicate_args, predicate_kwargs = match_fn(tokens)
            if match_success:
                predicate_fn(*predicate_args, **predicate_kwargs)
                return passed_rule(advance, next_state)
            return failed_rule()
        return impl

    @_compile_rule.method(dict)
    def _compile_dict_rule(self, rule):
        '''
        Compiler dispatch function for dict-based rules.  Returns a function
        that processes zero or more tokens, and returns a passed/failed rule 
        tuple as a result.
        '''

        def impl(tokens):
            tok = tokens[0]
            if tok in rule:
                predicate_fn, next_state = rule[tok]
                predicate_fn(tok)
                return passed_rule(1, next_state)
            return failed_rule()
        return impl

    @singledispatch
    def _compile_match(self, tok):
        '''
        Default function for compiling match functions.  Raises an exception
        as no other dispatchable types were matched.
        '''

        raise CompileError('Match expression is not callable', tok)
    
    @_compile_match.method(Callable)
    def _compile_match_callable(self, tok):
        '''
        Returns the provided match callable as a match function.
        '''
        assert(callable(tok))
        return tok

    @_compile_match.method(str)
    @_compile_match.method(unicode)
    def _compile_match_str(self, tok):
        '''
        Returns a match function for string and unicode values.
        '''

        def impl(tokens):
            if tokens[0] == tok:
                return passed_match(1, (tokens[0],))
            return failed_match()
        return impl

    def reset(self):
        '''
        Clears any internal state, resetting the parser back to the initial
        parse state.
        '''

        self._state = self._start_state
        self._pos = 0
        self._seq = []
        self._rule = 0

    def parse(self, sequence=None, state=None, position=0):
        '''
        Parses `sequence`, using the curent state machine configuration.  The
        parser will attempt to match all tokens in `tokens`, running to exhasution.
        Failure to exhaust all tokens will result in an error.

        This may be called using an alternate starting state, `state`,
        than the one configured in the constructor. 
        '''
        self._state = state or self._state
        self._pos = position or self._pos
        self._seq = sequence or self._seq
        while self._pos < len(self._seq):
            self._rule = 0
            for rule_fn in self.spec[self._state]:
                sub_sequence = self._seq[self._pos:]
                success, advance, next_state = rule_fn(sub_sequence)
                if success:
                    self._pos += advance
                    self._state = next_state
                    break
                self._rule += 1
            else:  # TODO: elif not partial  # partial matching support
                raise ParseError('No match found')

    @property
    def pos(self):
        '''
        Returns a string for the current position of the parser.
        '''

        return self._pos

    @property
    def tok(self):
        '''
        Returns the token at the current position of the parser.
        '''

        return self._seq[self._pos] if self._pos < len(self._seq) else None

    @property
    def state(self):
        '''
        Returns the current state of the parser.
        '''

        return self._state

    @property
    def rule(self):
        '''
        Returns the rule index within the current state of the parser
        '''

        return self._rule

    @property
    def status(self):
        '''
        Returns a dict containing all the state values.  Suitable for use
        with `str.format()` as kwargs.
        '''

        keys = ['pos', 'tok', 'state', 'rule']
        return dict(zip(keys, map(lambda x: getattr(self, x), keys)))


def match_any(tokens):
    '''
    Matches any single token.
    '''

    return passed_match(1, (tokens[0],))


def match_peek(tokens):
    '''
    Matches any single token, but does not advance the parser.  May be used in
    conjunction with `nop` to move the parser to a different state.
    '''

    return passed_match(0, (tokens[0],))


def match_set(value_set):
    '''
    Matches if a token matches any one value in `value_set`, by using the `in` 
    operator.  The `value_set` may be any object that implements `__in__`.
    '''

    def impl(tokens):
        tok = tokens[0]
        if tok in value_set:
            return passed_match(1, (tok,))
        return failed_match()
    return impl


def match_all(seq):
    '''
    Matches against the entire sequence and passes it to the predicate.
    May also be used in conjunction with `nop` to exhaust the parser.
    '''

    return passed_match(len(seq), (seq,))


# TODO: change to head match
def match_str(tok):
    '''
    Match function that matches a string against multiple successive character
    tokens.
    '''

    tok_len = len(tok)
    def impl(tokens):
        if tokens[:tok_len] == tok:
            return passed_match(tok_len, (tok,))
        return failed_match()
    return impl

# TODO: change to subsequence match
def match_multi(*values):
    values_len = len(values)
    def impl(tokens):
        if tokens[:values_len] == values:
            return passed_match(values_len, (tokens[:values_len],))
        return failed_match()
    return impl


def match_rex(expr):
    '''
    Match function that matches a regular expression against multiple character
    tokens.  The resulting groups and groupdict are passed to the predicate
    as *args and **kwargs, respectively, if there's a match.
 
    NOTE: will only work with sequeneces of type 'str' and 'unicode', as the entire
    sequence is passed directly to a compiled regex type (see `re` library).
    '''

    rex = re.compile(expr)
    def impl(tokens):
        result = rex.match(tokens)
        if result:
            return passed_match(result.end(), result.groups(), result.groupdict())
        return failed_match()
    return impl


class RexParser(Parser):
    '''
    Parser implementation that treats all string match types as regular expressions.

    Overrides the match function compilation for `str` and `unicode` and maps them
    both to `match_rex()`.

    This parser will only accept string type sequences.
    '''

    _compile_match = Parser._compile_match.clone()

    @_compile_match.method(str)
    @_compile_match.method(unicode)
    def _compile_match_rex(self, tok):
        return match_rex(tok)

    def parse(self, sequence):
        if not isinstance(sequence, str) and not isinstance(sequence, unicode):
            raise Exception('RexParser expects string or buffer (got {} instead)'.format(type(sequence)))
        return super(RexParser, self).parse(sequence)
