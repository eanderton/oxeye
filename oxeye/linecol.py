from __future__ import unicode_literals, absolute_import

from oxeye.parser import Parser
from oxeye.match import match_any

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


class LineColErrorMixin(object):
    # TODO: wrap parse() and provide properties instead
    
    def _error(self, position, state, tokens, msg, nested):
        line, col = pos_to_linecol(tokens, position)
        new_msg = '{} ({}, {}): Error at parse state "{}": {} ({})'.format(position, line, col, state, msg, tokens)
        raise ParseError(position, state, tokens, new_msg, nested)
