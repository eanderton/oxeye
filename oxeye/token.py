# -*- coding: utf-8 -*-
'''
Oxeye Parser library for Token-based implementations.
'''

from functools import singledispatchmethod
from collections.abc import Callable
from oxeye.parser import Parser, ParseError, PositionMixin
from oxeye.parser import match_head


class Token(object):
    '''
    Token implementation used with TokenParser.  Provides an abstraction of a lexeme
    as parsed from a stream, with optional line and column information.
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

    def __hash__(self):
        '''
        Override for hash magic to allow tokens to match to string names, and to
        allow value-oriented tokens to match cleanly.
        '''
        return self.name.__hash__()

    def __eq__(self, other):
        '''
        Override to allow for hashing of this type, as well as equality with
        string types.  Equates `self.name` to other token names or string contents.
        '''

        if isinstance(other, str):
            return str(self.name) == other
        return self.name == other.name

    def __call__(self, value=None, line=0, column=0):
        '''
        Returns a new token that shares the same name as self.
        '''
        return Token(self.name, value, line, column)


class TokenParser(Parser):
    '''
    Parser implementation for Token type streams.  Provides properties for diagnostic
    output based on the last parsed Token.
    '''

    _status_keys = Parser._status_keys + ['line', 'column']

    @singledispatch
    def _compile_match(self, *args, **kwargs):
        return super(TokenParser, self)._compile_match(*args, **kwargs)

    @_compile_match.method(Token)
    def _compile_match_token(self, tok):
        return match_head(tok)

    @property
    def line(self):
        '''
        Returns the current token line positiion.
        '''

        return self.head.line if self.head and hasattr(self.head, 'line') else None

    @property
    def column(self):
        '''
        Returns the current token column position.
        '''

        return self.head.column if self.head and hasattr(self.head, 'column') else None


class TokenLexer(Parser, PositionMixin):
    '''
    Lexer implementation that converts parsed input into a series of Token instances.

    The tokens are available via `self._tokens` after a call to `parse()`.
    '''

    _status_keys = Parser._status_keys + PositionMixin._position_status_keys

    def reset(self):
        '''
        Override that resets Lexer properties as well as base class properties.
        '''

        super(TokenLexer, self).reset()
        self._reset_position()
        self._tokens = []

    def _error(self, position, state, tokens, msg, nested):
        msg = '({}, {}) {}'.format(self.line, self.column, msg)
        raise ParseError(position, state, tokens, msg, nested)

    def _token(self, value, token_type=Token):
        '''
        Predicate function that creates a new token of the given type for `value`.
        '''

        self._tokens.append(token_type(value, line=self._line, column=self._column))
        self._column += len(value)

    def _token_as(self, token_type):
        '''
        Returns a predicate function that wraps `_token()` with a specified Token type.
        '''

        def impl(value):
            return self._token(value, token_type)
        return impl

    @property
    def tokens(self):
        '''
        The list of all tokens parsed by this lexer.
        '''

        return self._tokens
