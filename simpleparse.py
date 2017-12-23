import re
import copy

def nop(*args, **kwargs):
    """
    Does nothing. Intended for do-nothing terminals in a DFA spec.
    """
    pass 


def err(msg):
    def impl():
        raise Exception(msg)
    return impl



class Token(object):
    def __init__(self, name, value=None):
        self.name = name
        self.value = value or name

    def match(self, other):
        return self.name == other.name, 1, (other.value,), {}

    def __call__(self, value=None):
        other = copy.copy(self)
        other.value = value or other.name
        return other

    def __eq__(self, other):
        return self.name == other.name


class _TokenAny(Token):
    def match(self, other):
        return True, 1, (other.value,), {}


Token.any = _TokenAny(None)


class _TokenAnyLookahead(Token):
    def match(self, other):
        return True, 0, (other.value,), {}


Token.any_lookahead = _TokenAnyLookahead(None)



class ParseError(Exception):
    def __init__(self, position, state, text, message):
        self.position = position
        self.state = state
        self.text = text
        Exception.__init__(self, message)


class RexParser(object):
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


class TokenParser(object):
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
        def next_col():
            self.column += 1

        def next_line():
            self.column = 0
            self.line += 1

        self.dfa = RexParser({
            'body': (
                (r'\n', next_line, 'body'),
                (r'.', next_col, 'body'),
            ),
        })

    def __call__(self, text, position=None):
        self.column = 1
        self.line = 1
        if position is None:
            position = len(text)
        self.dfa.parse('body', text[:position])
        return self.line, self.column


def pos_to_linecol(text, position=None):
    return LineColTranslator()(text, position) 

