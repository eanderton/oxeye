import re
import copy

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
    def __init__(self, name, value=None, line=1, column=1):
        self.name = name
        self.value = value or name
        self.line = line
        self.column = column

    def copy(self, value=None):
        other = copy.copy(self)
        other.value = value or other.name
        return other

    def __eq__(self, other):
        return self.name == other.name


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
        if callable(tok):
            return tok
        def impl(tokens):
            return MatchResult(tokens[:len(tok)] == tok, len(tok), (tok,))
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
                for match_fn, fn, next_state in self.spec[self.state]:
                    result = match_fn(tokens[position:])
                    if result.success:
                        fn(*result.args, **result.kwargs)
                        position += result.advance
                        self.state = next_state
                        break  # leave test loop
                else:
                    self._error(position, self.state, tokens, 'No match found', None)
        except Exception as e:
            self._error(position, self.state, tokens, str(e), e)


def match_any(tokens):
    return MatchResult(True, 1, (tokens[0],))


def match_peek(tokens):
    return MatchResult(True, 0, (tokens[0],))


def match_range(tokens, value_range):
    tok = tokens[0]
    return matchResult(tok in value_range, len(tok), (tok,))


def match_all(tokens):
    return MatchResult(true, len(tokens), (tokens,))


class RexParser(Parser):
    def _compile(self, tok):
        if callable(tok):
            return tok
        rex = re.compile(tok)
        def impl(tokens):
            result = rex.match(tokens)
            if result:
                return MatchResult(True, result.end(), result.groups(), result.groupdict())
            return MatchResult(False)
        return impl

    def _error(self, position, state, tokens, msg, nested):
        line, col = pos_to_linecol(tokens, position)
        new_msg = '{} ({}, {}): Error at parse state "{}": {} ({})'.format(position, line, col, state, msg, tokens)
        raise ParseError(position, state, tokens, new_msg, nested)


class TokenParser(Parser):
    def _compile(self, tok):
        if callable(tok):
            return tok
        def impl(tokens):
            other = tokens[0]
            return MatchResult(tok.name == other.name, 1, (other.value,))
        return impl


class __RexParser(object):
    def __init__(self, spec):
        self.spec = {}
        for state, tests in spec.iteritems():
            compiled_tests = []
            for rex, fn, next_state in tests:
                compiled_tests.append((re.compile(rex), fn, next_state))
            self.spec[state] = compiled_tests


    def parse(self, state, text):
        position = 0
        while position < len(text):
            for rex, fn, next_state in self.spec[state]:
                result = rex.match(text[position:])
                if result:
                    fn(*result.groups(), **result.groupdict())
                    position += result.end()
                    state = next_state
                    break  # leave test loop
            else:
                raise ParseError(position, state, text, 'No match found')

    @classmethod
    def err_state(cls, msg):
        return (r'.', err(msg), None)

    @classmethod
    def next_state(cls, state):
        return (r'(?=.)', nop, state)


class __TokenParser(object):
    def __init__(self, spec):
        self.spec = {}
        for state, tests in spec.iteritems():
            compiled_tests = []
            for tok, fn, next_state in tests:
                compiled_tests.append((tok.match, fn, next_state))
            self.spec[state] = compiled_tests

    def parse(self, state, tokens):
        position = 0
        while position < len(tokens):
            for cmp_fn, fn, next_state in self.spec[state]:
                result, advance, groups, groupdict = cmp_fn(tokens[position])
                if result:
                    fn(*groups, **groupdict)
                    position += advance
                    state = next_state
                    break  # leave test loop
            else:
                raise ParseError(position, state, text, 'No match found')

    @classmethod
    def err_state(cls, msg):
        return (Token.any, err(msg), None)

    @classmethod
    def next_state(cls, state):
        return (Token.any_lookahead, nop, state)



class LineColTranslator(object):
    def __init__(self):
        def next_col(value):
            self.column += 1

        def next_line(value):
            self.column = 0
            self.line += 1

        self.dfa = Parser({
            'goal': (
                ('\n', next_line, 'goal'),
                (match_any, next_col, 'goal'),
            ),
        })

    def parse(self, text, position=None):
        self.column = 1
        self.line = 1
        if position is None:
            position = len(text)
        self.dfa.parse(text[:position])
        return self.line, self.column


def pos_to_linecol(text, position=None):
    return LineColTranslator().parse(text, position)
