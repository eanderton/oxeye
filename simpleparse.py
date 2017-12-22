import re
import collections

def nop(*args, **kwargs):
    """
    Does nothing. Intended for do-nothing terminals in a DFA spec.
    """
    pass 


class ParseError(Exception):
    def __init__(self, position, state, text, message):
        self.position = position
        self.state = state
        self.text = text
        Exception.__init__(self, message)


class DFAParser(object):
    def __init__(self, spec):
        self.spec = {}
        for state, tests in spec.iteritems():
            compiled_tests = []
            for rex, fn, next_state in tests:
                compiled_tests.append((re.compile(rex), fn, next_state))
            self.spec[state] = compiled_tests


    def parse(self, state, text, position=0):
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



class LineColTranslator(object):
    def __init__(self):
        def next_col():
            self.column += 1

        def next_line():
            self.column = 0
            self.line += 1

        self.dfa = DFAParser({
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

