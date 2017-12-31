# -*- coding: utf-8 -*-
'''
Oxeye Parser library for Token-based implementations. 
'''

from __future__ import unicode_literals, absolute_import
from oxeye.multimethods import enable_descriptor_interface, singledispatch
from oxeye.multimethods_ext import Callable, patch_multimethod_extend
from oxeye.parser import Parser, ParseError, failed_match, passed_match

enable_descriptor_interface()
patch_multimethod_extend()


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


def match_token(value):
    '''
    Returns a match function that matches a single value or token against the head 
    of the parse sequence.
    '''

    if not isinstance(value, Token):
        value = Token(value)
    def impl(tokens):
        tok = tokens[0]
        if tok == value:
            return passed_match(1, (tok,))
        return failed_match()
    return impl


class TokenParser(Parser):
    '''
    Parser implementation for Token type streams.  Provides support for Token subclasses
    as match expressions in the parser specification.
    '''

    _compile_match = Parser._compile_match.extend()

    def _error(self, position, tokens, msg):
        '''
        Override for `Parser._error()`. Adds line and column information to error message.
        '''
        
        tok = tokens[position]
        msg = '({}, {}) {}'.format(tok.line, tok.column, msg) 
        raise ParseError(position, tokens, msg)

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
