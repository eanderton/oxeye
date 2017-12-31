# -*- coding: utf-8 -*-
'''
Oxeye Parser library.  Provides utility classes and functions for constructing
discrete state machines for parsing text or a token stream.
'''

from __future__ import unicode_literals, absolute_import

import re
from oxeye.multimethods import enable_descriptor_interface, singledispatch
from oxeye.multimethods_ext import Callable, String, patch_multimethod_clone
from oxeye.match import match_head, match_rex
from oxeye.rule import failed_rule, passed_rule
from oxeye.pred import *

enable_descriptor_interface()
patch_multimethod_clone()


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
    def __init__(self, parser, *args, **kwargs):
        super(CompileError, self).__init__(*args, **kwargs)
        self.parser = parser


class Parser(object):
    '''
    Core parser class.  Implements a token based parser based on a provided parser
    specification (`spec`).  The parser operates on an input set of tokens, that 
    may be any indexable type, including `str` or `unicode`.

    '''

    # TODO implement end states
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
                    raise CompileError(self, 'Rule must compile to a callable object')
                self.spec[self._state].append(rule)
        # TODO: semantic checking of next_state validity
        self.reset()


    @singledispatch
    def _compile_rule(self, rule):
        '''
        Default dispatch function for compiling rules.  Raises an exception as
        no other dispatchable types were matched.
        '''

        raise CompileError(self, 'No registered method to compile rule')

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
            raise CompileError(self, 'Rule match function must compile to a callable object')
        def impl(tokens):
            match_success, advance, predicate_args, predicate_kwargs = match_fn(tokens)
            if match_success:
                predicate_fn(*predicate_args, **predicate_kwargs)
                return passed_rule(advance, next_state)
            return failed_rule()
        return impl

    @_compile_rule.method(dict)
    def _compile_dict_rule(self, rule_dict):
        '''
        Compiler dispatch function for dict-based rules.  Returns a function
        that processes zero or more tokens, and returns a passed/failed rule 
        tuple as a result.
        '''

        # TODO: semantic pass on rule_dict
        def impl(sequence):
            head = sequence[0]
            rule = rule_dict.get(head, None)
            if rule:
                predicate_fn, next_state = rule
                predicate_fn(head)
                return passed_rule(1, next_state)
            return failed_rule()
        return impl

    @singledispatch
    def _compile_match(self, value):
        '''
        Default function for compiling match functions.  Raises an exception
        as no other dispatchable types were matched.
        '''

        raise CompileError(self, 'Match expression "{}" is not callable'.format(value))
    
    @_compile_match.method(Callable)
    def _compile_match_callable(self, fn):
        '''
        Returns the provided match callable as a match function.
        '''
        return fn

    @_compile_match.method(String)
    def _compile_match_str(self, value):
        '''
        Returns a match function for string and unicode values.
        '''
        return match_head(value)

    def reset(self):
        '''
        Clears any internal state, resetting the parser back to the initial
        parse state.
        '''

        self._state = self._start_state
        self._pos = 0
        self._seq = []
        self._rule = 0

    def parse(self, sequence=None, state=None, position=0, exhaustive=True):
        '''
        Parses a sequence of elements, using the curent state machine configuration.
        Each parameter overrides an aspect of this state, allowing for partial
        parse passes, starting from an alternate state or position, and running
        the parser to exhaustion.

        Returns True if the sequence was entirely parsed (exhausted), False if not.

        The default state, position, and sequence, in a newly constructed parser
        are set to `start_state`, `0`, and `[]` respectively.  Additionally, these 
        are guaranteed by any call to `reset()`.

        The `exhaustive` argument is set to True by default.  The parser will
        raise ParseError if it cannot match a rule against the sequence in the
        current state.

        Providing `sequence` will parse against the provided sequence, starting
        at the current position and state.

        Providing `state` will start the parse at the provided state instead of 
        the current state.

        Providing `position` will start the parse at the provided position in the
        sequence instead of the current position.
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
            else:
                if exhaustive:  
                    raise ParseError('No match found')
                return False
        return True

    @property
    def pos(self):
        '''
        Returns a string for the current position of the parser.
        '''

        return self._pos

    @property
    def head(self):
        '''
        Returns the token at the current position of the parser.
        '''

        return self._seq[self._pos] if self._seq and self._pos < len(self._seq) else None

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

        keys = ['pos', 'head', 'state', 'rule']
        return { x: getattr(self, x) for x in keys }


class RexParser(Parser):
    '''
    Parser implementation that treats all string match types as regular expressions.

    Overrides the match function compilation for `str` and `unicode` and maps them
    both to `match_rex()`.

    This parser will only accept string type sequences.
    '''

    _compile_match = Parser._compile_match.clone()

    @_compile_match.method(String)
    #@_compile_match.method(str)
    #@_compile_match.method(unicode)
    def _compile_match_rex(self, tok):
        return match_rex(tok)

    def parse(self, sequence):
        if not isinstance(sequence, str) and not isinstance(sequence, unicode):
            raise Exception('RexParser expects string or buffer (got {} instead)'.format(type(sequence)))
        return super(RexParser, self).parse(sequence)
