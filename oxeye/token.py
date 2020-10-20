# -*- coding: utf-8 -*-
'''
Oxeye Parser library for Token-based implementations.
'''

import copy
from functools import singledispatchmethod
from collections.abc import Callable
from oxeye.parser import Parser, ParseError, PositionMixin
from oxeye.parser import match_head


class Token(object):
    '''
    Token implementation used with TokenParser.  Provides an abstraction of a lexeme
    as parsed from a stream, with optional line and column information.
    '''

    def __init__(self, name, value=None, source=None, line=0, column=0):
        '''
        Token constructor.  Specifies a token instance with a given name, value, and
        optional line and column information.
        '''

        self.name = name
        self.value = value or name
        self.source = source
        self.line = line
        self.column = column

    def __str__(self):
        '''
        String representation of the token.  Used for debugging.
        '''

        return f'Token({self.name}) {self.source} ({self.line}, {self.column}): {self.value}'

    __repl__ = __str__

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

    def __call__(self, value=None, source=None, line=0, column=0):
        '''
        Returns a new token that shares the same name as self.
        '''
        return Token(self.name, value, source, line, column)


class TokenParser(Parser):
    '''
    Parser implementation for Token type streams.  Provides properties for diagnostic
    output based on the last parsed Token.
    '''

    _status_keys = Parser._status_keys + ['line', 'column']

    def _parse_error(self, message):
        tok = self.head
        super()._parse_error(f'{tok.source} ({tok.line}, {tok.column}): {message}')

    @singledispatchmethod
    def _compile_match(self, *args, **kwargs):
        return super()._compile_match(*args, **kwargs)

    @_compile_match.register
    def _compile_match_token(self, tok: Token):
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

    def _parse_error(self, message):
        '''
        Override that generates an error message with source, line, and column info
        '''
        super()._parse_error(f'{self._source} ({self._line}, {self._column}): {message}')

    @singledispatchmethod
    def _resolve_predicate(self, *args, **kwargs):
        '''
        Proxies all other predicate types to the superclass dispatch method.
        '''
        return super()._resolve_predicate(*args, **kwargs)

    @_resolve_predicate.register
    def _resolve_predicate_token(self, pred: Token):
        '''
        Resolves a predicate for a single token value
        '''
        def impl(value):
            return self._token(value, pred)
        return impl

    def reset(self):
        '''
        Override that resets Lexer properties as well as base class properties.
        '''

        super().reset()
        self._reset_position()
        self._tokens = []
        self._source = None

    def _push_token(self, tok):
        '''
        Pushes a single token and sets the current line and column.
        '''
        tok.line = self._line
        tok.column = self._column
        tok.source = self._source
        self._tokens.append(tok)

    def _token(self, value, token_type=Token, length=None):
        '''
        Predicate function that creates a new token of the given type for `value`.
        '''

        tok = token_type(value)
        self._push_token(tok)

        if length is not None:
            self._column += length
        else:
            self._column += len(value)

    @property
    def tokens(self):
        '''
        The list of all tokens parsed by this lexer.
        '''

        return self._tokens

    def parse(self, sequence=None, state=None, position=0, exhaustive=True, source=None):
        '''
        Parses a sequence of elements.

        See documentation for oxeye.parser.Parser.  This override takes an extra argument for
        a source name.  This is used when constructing new tokens and generating error messages.
        '''
        self._source = source
        super().parse(sequence, state, position, exhaustive)
