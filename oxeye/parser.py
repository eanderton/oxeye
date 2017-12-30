# -*- coding: utf-8 -*-
'''
Oxeye Parser library.  Provides utility classes and functions for constructing
discrete state machines for parsing text or a token stream.
'''

from __future__ import unicode_literals, absolute_import

import re
import copy
import inspect
from oxeye.multimethods import enable_descriptor_interface, singledispatch
from oxeye.multimethods_ext import Callable, patch_multimethod_extend


enable_descriptor_interface()
patch_multimethod_extend()


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


class Token(object):
    '''
    Token implementation used with TokenParser.  Provides an abstraction of a lexeme
    as parsed from a stream, with optional line and column information.

    Token types (subclasses) can be created by using the `Token.factory()` method. 
    '''

    def __init__(self, name, value=None, line=0, column=0):
        '''
        Token constructor.  Specifies a token instance with a given name, value, and
        optional line and column information.
        '''

        self.name = name
        self.value = value or name
        self.line = line
        self.column = column

    def __str__(self):
        '''
        String representation of the token.  Used for debugging.
        '''

        return 'Token({}, {}, {}, {})'.format(self.name, self.value, self.line, self.column)

    __unicode__ = __str__

    def __hash__(self):
        '''
        Override for hash magic to allow tokens to match to string names, and to
        allow value-oriented tokens to match cleanly.
        '''
        return self.name.__hash__()

    def __eq__(self, other):
        if isinstance(other, str):
            return str(self.name) == other
        if isinstance(other, unicode):
            return unicode(self.name) == other
        return self.name == other.name

    def __call__(self, value=None, line=0, column=0):
        '''
        Returns a new token that shares the same name as self.
        '''
        return Token(self.name, value, line, column)


class ParseError(Exception):
    '''
    Base error type for parse related errors.  May optionally include a nested
    exception if another exception was the cause for the error.
    '''

    def __init__(self, position, state, text, message, nested_exception=None):
        self.position = position
        self.state = state
        self.text = text
        self.nested_exception = nested_exception
        Exception.__init__(self, message)


class CompileError(Exception):
    '''
    Error type for compilation-based errors.
    '''

    def __init__(self, subject=None, state=None):
        self.subject = subject
        self.state = state


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
          See the module documentation for more information on rules.
        '''
        self.spec = {}
        self.start_state = start_state
        try:
            for state, tests in spec.iteritems():
                self.spec[state] = map(self._compile_rule, tests)
        except CompileError as e:
            e.state = state
            raise
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
        return tok

    @_compile_match.method(str)
    @_compile_match.method(unicode)
    def _compile_match_str(self, tok):
        '''
        Returns a match function for string and unicode values.
        '''

        def impl(tokens):
            if tokens[0] == tok:
                return passed_match(1, (tok,))
            return failed_match()
        return impl

    def _error(self, position, state, tokens, msg, nested):
        '''
        Raises an error.  This method is used by `parse()`, and should be
        overridden if different error generation behavior is desired.
        '''

        raise ParseError(position, state, tokens, msg, nested)

    def reset(self):
        '''
        Clears any internal state, resetting the parser back to the initial
        parse state.
        '''

        self.state = self.start_state

    def parse(self, tokens, state_override=None):
        '''
        Parses over tokens, using the curent state machine configuration.  The
        parser will attempt to match all tokens in `tokens`, running to exhasution.
        Failure to exhaust all tokens will result in an error.

        This may be called using an alternate starting state, `state_override`,
        than the one configured in the constructor.  
        '''
        self.state = state_override or self.state
        position = 0
        try:
            while position < len(tokens):
                for test_fn in self.spec[self.state]:
                    success, advance, next_state = test_fn(tokens[position:])
                    if success:
                        position += advance
                        self.state = next_state
                        break
                else:
                    self._error(position, self.state, tokens, 'No match found', None)
        except Exception as e:
            self._error(position, self.state, tokens, unicode(e), e)


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


def match_token(value):
    value_tok = Token(value)
    def impl(tokens):
        tok = tokens[0]
        if tok == value_tok:
            return passed_match(1, (tok,))
        return failed_match()
    return impl

def match_all(tokens):
    '''
    Matches against all remaining input tokens and passes them to the predicate.
    May also be used in conjunction with `nop` to exhasut the parser.
    '''

    return passed_match(len(tokens), (tokens,))


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
    '''

    _compile_match = Parser._compile_match.extend()

    @_compile_match.method(str)
    @_compile_match.method(unicode)
    def _compile_match_rex(self, tok):
        return match_rex(tok)


class TokenParser(Parser):
    '''
    Parser implementation for Token type streams.  Provides support for Token subclasses
    as match expressions in the parser specification.
    '''

    _compile_match = Parser._compile_match.extend()

    def _error(self, position, state, tokens, msg, nested):
        '''
        Override for `Parser._error()`. Adds line and column information to error message.
        '''
        
        tok = tokens[position]
        msg = '({}, {}) {}'.format(tok.line, tok.column, msg) 
        raise ParseError(position, state, tokens, msg, nested)

    @_compile_match.method(str)
    @_compile_match.method(unicode)
    def _compile_match_str(self, tok):
        return match_token(tok)
    
    @_compile_match.method(Token)
    def _compile_match_token(self, tok):
        def impl(tokens):
            other = tokens[0]
            if tok == other:
                return passed_match(1, (other.value,))
            return failed_match()
        return impl
