# -*- coding: utf-8 -*-
'''
Oxeye Parser library for Token-based implementations. 
'''

from __future__ import unicode_literals, absolute_import
from oxeye.multimethods import enable_descriptor_interface, singledispatch
from oxeye.multimethods_ext import Callable, patch_multimethod_clone
from oxeye.parser import Parser, ParseError, match_head

enable_descriptor_interface()
patch_multimethod_clone()


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

    __unicode__ = __str__

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
        if isinstance(other, unicode):
            return unicode(self.name) == other
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

    _compile_match = Parser._compile_match.clone()

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

    @property
    def status(self):
        '''
        Returns a dict containing all the state values.  Suitable for use
        with `str.format()` as kwargs.

        Overidden to include `line` and `column` properties.
        '''

        result = super(TokenParser, self).status
        keys = ['line', 'column']
        result.update(dict(zip(keys, map(lambda x: getattr(self, x), keys))))
        return result


class TokenLexer(Parser):
    '''
    Lexer implementation that converts parsed input into a series of Token instances.

    The tokens are available via `self._tokens` after a call to `parse()`.
    '''

    def reset(self):
        '''
        Override that resets Lexer properties as well as base class properties.
        '''

        super(TokenLexer, self).reset()
        self._tokens = []
        self._line = 1
        self._column = 1
    
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

    def _whitespace(self, value):
        '''
        Predicate function that increments the column count by value
        '''

        self._column += len(value)

    def _newline(self, value):
        '''
        Predicate function that increments the line by one, and resets the column to 1.
        '''

        self._column = 1
        self._line += 1

    @property
    def tokens(self):
        '''
        The list of all tokens parsed by this lexer.
        '''

        return self._tokens

    @property
    def line(self):
        '''
        Returns the current token line positiion.
        '''

        return self._line
    
    @property
    def column(self):
        '''
        Returns the current token column position.
        '''

        return self._column

    @property
    def status(self):
        '''
        Returns a dict containing all the state values.  Suitable for use
        with `str.format()` as kwargs.

        Overidden to include `line` and `column` properties.
        '''

        result = super(TokenLexer, self).status
        keys = ['line', 'column']
        result.update(dict(zip(keys, map(lambda x: getattr(self, x), keys))))
        return result


