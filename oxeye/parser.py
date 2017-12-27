# -*- coding: utf-8 -*-
'''
Oxeye Parser library.
'''

from __future__ import unicode_literals, absolute_import

import re
import copy
import inspect
from oxeye import multimethods

multimethods.enable_descriptor_interface()


def _multimethod_extend_patch(self, dispatch_func=None):
    '''
    Creates a new multimethod that extends this multimethod, by chaining
    to this multimethod on default.  
    
    Can be called using an optional dispatch function `dispatch_func` for 
    the newly created multimethod.
    '''

    def default_impl(*args, **kwargs):
        return self.__call__(*args, **kwargs)
    dispatch_func = dispatch_func or self.dispatchfn
    pass_self = self.pass_self
    mm = multimethods.MultiMethod(self.__name__, dispatch_func, pass_self)
    mm.add_method(multimethods.Default, default_impl)
    return mm


multimethods.MultiMethod.extend = _multimethod_extend_patch


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
        self.name = name
        self.value = value or name
        self.line = line
        self.column = column

    def __str__(self):
        return 'Token({}, {}, {}, {})'.format(self.name, self.value, self.line, self.column)

    __unicode__ = __str__

    @classmethod
    def factory(cls, name, value_fn=None):
        if value_fn:
            class TokenImpl(Token):
                def __init__(self, value, line=0, column=0):
                    Token.__init__(self, name, value_fn(value), line, column)
        else:
            class TokenImpl(Token):
                def __init__(self, value, line=0, column=0):
                    Token.__init__(self, name, value, line, column)
        return TokenImpl


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


class MatchResult(object):
    '''
    Represents a parser match for one or more input tokens. Used by match functions
    during a parser pass.
    '''

    def __init__(self, success, advance=1, args=None, kwargs=None):
        self.success = success
        self.advance = advance
        self.args = args or ()
        self.kwargs = kwargs or {}

class Parser(object):
    '''
    Core parser class.  Implements a token based parser based on a provided parser
    specification (`spec`).  The parser operates on an input set of tokens, that 
    may be any indexable type, including `str` or `unicode`.
    '''

    def __init__(self, spec, start_state='goal'):
        self.spec = {}
        for state, tests in spec.iteritems():
            self.spec[state] = map(self._compile_rule, tests)
        self.start_state = start_state
        self.reset()


    @multimethods.singledispatch
    def _compile_rule(self, rule):
        raise Exception('Error during compilation: no registered method to compile "{}"'.format(rule))

    @_compile_rule.method(tuple)
    def _compile_tuple_rule(self, rule):
        match_tok, predicate_fn, next_state = rule
        match_fn = self._compile_match(match_tok)
        def impl(tokens):
            result = match_fn(tokens)
            if not result.success:
                return False, 0, None
            predicate_fn(*result.args, **result.kwargs)
            return True, result.advance, next_state
        return impl

    #@_compile_rule.method(dict)
    #def _compile_dict_rule(self, rule):
    #    pass

    @multimethods.singledispatch
    def _compile_match(self, tok):
        if not callable(tok):
            raise Exception('Error during compilation: "{}" is not callable'.format(tok))
        return tok

    @_compile_match.method(str)
    @_compile_match.method(unicode)
    def _compile_match_str(self, tok):
        def impl(tokens):
            return MatchResult(tokens[0] == tok, 1, (tok,))
        return impl

    def _error(self, position, state, tokens, msg, nested):
        raise ParseError(position, state, tokens, msg, nested)

    def reset(self):
        self.state = self.start_state

    def parse(self, tokens, state_override=None):
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
    Matches 
    '''
    return MatchResult(True, 1, (tokens[0],))


def match_peek(tokens):
    return MatchResult(True, 0, (tokens[0],))


def match_range(value_range):
    def impl(tokens):
        tok = tokens[0]
        return MatchResult(tok in value_range, 1, (tok,))
    return impl


def match_all(tokens):
    return MatchResult(True, len(tokens), (tokens,))


def match_str(tok):
    tok_len = len(tok)
    def impl(tokens):
        return MatchResult(tokens[:tok_len] == tok, tok_len, (tok,))
    return impl


def match_rex(expr):
    rex = re.compile(expr)
    def impl(tokens):
        result = rex.match(tokens)
        if result:
            return MatchResult(True, result.end(), result.groups(), result.groupdict())
        return MatchResult(False)
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


def _token_type_dispatch(*args, **kwargs):
    '''
    Multimethod dispatch function for TokenParser.  Allows registered multimethods to 
    match on the 'Token' type, if a subclass of that type is provided.
    '''

    tok = args[0]
    if inspect.isclass(tok) and issubclass(tok, Token):
        return Token
    return type(tok)


class TokenParser(Parser):
    '''
    Parser implementation for Token type streams.  Provides support for Token subclasses
    as match expressions in the parser specification.
    '''

    _compile_match = Parser._compile_match.extend(_token_type_dispatch)

    @_compile_match.method(Token)
    def _compile_match_token(self, tok):
        def impl(tokens):
            other = tokens[0]
            return MatchResult(isinstance(other, tok), 1, (other.value,))
        return impl
