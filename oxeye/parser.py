from __future__ import unicode_literals, absolute_import

import re
import copy
import inspect


def nop(*args, **kwargs):
    '''
    Terminal function that does nothing. Intended for do-nothing terminals in a DFA spec.
    '''
    pass 


def err(msg):
    '''
    Terminal function that emits an exception for `msg`.
    '''
    def impl(*args, **kwargs):
        raise Exception(msg)
    return impl


class Token(object):
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
    def __init__(self, position, state, text, message, nested_exception=None):
        self.position = position
        self.state = state
        self.text = text
        self.nested_exception = nested_exception
        Exception.__init__(self, message)


class MatchResult(object):
    def __init__(self, success, advance=1, args=None, kwargs=None):
        self.success = success
        self.advance = advance
        self.args = args or ()
        self.kwargs = kwargs or {}


class Parser(object):
    def __init__(self, spec, start_state='goal'):
        self.spec = {}
        for state, tests in spec.iteritems():
            compiled_tests = []
            for tok, fn, next_state in tests:
                compiled_tests.append((self._compile(tok), fn, next_state))
            self.spec[state] = compiled_tests

        self.start_state = start_state
        self.reset()

    def _compile(self, tok):
        if isinstance(tok, str) or isinstance(tok, unicode):
            def impl(tokens):
                return MatchResult(tokens[:len(tok)] == tok, len(tok), (tok,))
            return impl
        return tok

    def _error(self, position, state, tokens, msg, nested):
        raise ParseError(position, state, tokens, msg, nested)

    def reset(self):
        self.state = self.start_state

    def parse(self, tokens, state_override=None):
        self.state = state_override or self.state
        position = 0
        try:
            while position < len(tokens):
                for match_fn, predicate_fn, next_state in self.spec[self.state]:
                    result = match_fn(tokens[position:])
                    if result.success:
                        predicate_fn(*result.args, **result.kwargs)
                        position += result.advance
                        self.state = next_state
                        break  # leave test loop
                else:
                    self._error(position, self.state, tokens, 'No match found', None)
        except Exception as e:
            self._error(position, self.state, tokens, unicode(e), e)


def match_any(tokens):
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


def match_rex(expr):
    rex = re.compile(expr)
    def impl(tokens):
        result = rex.match(tokens)
        if result:
            return MatchResult(True, result.end(), result.groups(), result.groupdict())
        return MatchResult(False)
    return impl


class RexParser(Parser):
    def _compile(self, tok):
        if isinstance(tok, unicode) or isinstance(tok, str):
            return match_rex(tok)
        return tok


class TokenParser(Parser):
    def _compile(self, tok):
        if inspect.isclass(tok) and issubclass(tok, Token):
            def impl(tokens):
                other = tokens[0]
                return MatchResult(isinstance(other, tok), 1, (other.value,))
            return impl
        return tok


