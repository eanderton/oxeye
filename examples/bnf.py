from __future__ import unicode_literals, absolute_import
from oxeye.parser import (Token, Parser, TokenParser, nop, err, match_any, match_peek, 
                        match_set, match_all, match_rex)

class Tok(object):
    '''
    Containing namespace for token types.
    '''
    ident = Token.factory('ident')
    number = Token.factory('number', float)
    lparen = Token.factory('lparen')
    rparen = Token.factory('rparen')
    dash = Token.factory('dash')
    plus = Token.factory('plus')
    star = Token.factory('star')
    slash = Token.factory('slash')
    colon = Token.factory('colon')
    semi = Token.factory('semi')
    equal = Token.factory('equal')
    pipe = Token.factory('pipe')
    bang = token.factory('bang')
    string = Token.factory('string')


class TokenLexer(Parser):
    '''
    Lexer implementation that converts parsed input into a series of Token instances.

    The tokens are available via `self.tokens` after a call to `parse()`.
    '''

    def _error(self, position, state, tokens, msg, nested):
        msg = '({}, {}) {}'.format(self.line, self.column, msg) 
        raise ParseError(position, state, tokens, msg, nested)

    def reset(self):
        super(TokenLexer, self).reset()
        self.tokens = []
        self.line = 1
        self.column = 1
    
    def token(self, token_type):
        def impl(value):
            self.tokens.append(token_type(value, self.line, self.column))
            self.column += len(value)
        return impl

    def whitespace(self, value):
        self.column += len(value)

    def newline(self, value):
        self.column = 1
        self.line += 1


class BnfLexer(TokenLexer):
    '''
    Lexer for BNFParser. Seralizes a text stream into a list of tokens.
    Line and column information is gathered and attached to tokens as they are generated. 
    '''
    def __init__(self):
        super(BnfLexer, self).__init__({
            'goal': (
                (match_str('::='), self.token(Tok.rule_op), 'goal'),
                {
                    '(': (self.token(Tok.lparen), 'goal'),
                    ')': (self.token(Tok.rparen), 'goal'),
                    '-': (self.token(Tok.dash), 'goal'),
                    '+': (self.token(Tok.plus), 'goal'),
                    '*': (self.token(Tok.star), 'goal'),
                    '/': (self.token(Tok.slash), 'goal'),
                    ':': (self.token(Tok.colon), 'goal'),
                    ';': (self.token(Tok.semi), 'goal'),
                    '=': (self.token(Tok.equal), 'goal'),
                    '|': (self.token(Tok.pipe), 'goal'),
                    ' ': (self.whitespace, 'goal'),
                    '\r': (self.whitespace, 'goal'),
                    '\t': (self.whitespace, 'goal'),
                    '\v': (self.whitespace, 'goal'),
                    '\n': (self.newline, 'goal'),
                    '"': (self._string_start, 'string'),
                },
                (match_rex(r'"((?:\\.|[^"\\])*)"'), self.token(Tok.string), 'goal'),
                (match_rex(r'(#.*\n)'), self.token(Tok.whitespace), 'goal'),  # discard comments
                (match_rex(r'([_a-zA-Z][_a-zA-Z0-9]*)'), self.token(Tok.ident), 'goal'),
                (match_rex(r'(\d+(?:\.\d+)?)'), self.token(Tok.number), 'goal'),
                (match_any, err('unexpected token'), None),
            ),
        })


class AST(object):
    def __init__(self, name, line, column, children=[]):
        self.name = name
        self.line = line
        self.column = column
        self.children = children


class BnfGrammarParser(TokenParser):
    def __init__(self):
        super(BnfParser, self).__init__({
            'expr': (
                (match_multi(Tok.ident, Tok.colon, Tok.colon, Tok.equal), self._rule, 'rule')
                (match_any, err('Expected rule'), None)
            ),
            'rule': (
                (Tok.ident, self._rule_predicate, 'rule'),
                (Tok.string, self._rule_string, 'rule'),
                (Tok.pipe, self._rule_or, 'rule'),
                (Tok.semi, nop, 'expr'), 
                (match_any, err('Unexpected token in rule'), None)
            )
        }, 'expr')

    def _rule(self, tok_name, _, _, _):
        self.rule = AST('rule', tok.line, tok.column)
        self.root.children.append(self.rule)

    def reset(self):
        self.rule = None
        self.root = AST('root', 0, 0)
        super(BnfParser, self).reset()


    def parse(self, text):
        lexer = BnfLexer()
        lexer.parse(text)
        super(BnfParser, self).parse(lexer.tokens)
 

'''
<fullname> ::= <title>_<name>_<endtitle> |
               <name> |
               <title>_<name> |
               <name>_<endtitle>
<title> ::= MRS | MS | ... | SIR
<endtitle> ::= ESQUIRE | OBE | CBE
<name> ::= <word> |
           <name>_<word>
<word> ::= <char><
<char> ::= A | B | ... | Z
----
# annotate with AST operations
<fullname> ::= !push('fullname') (<title>_<name>_<endtitle> |
               <name> |
               <title>_<name> |
               <name>_<endtitle>)

<title> ::= !push (MRS | MS | ... | SIR) !store(title) | !pop()

<endtitle> ::= ESQUIRE | OBE | CBE

<name> ::= <word> |
           <name>_<word>

<word> ::= <char><word>

<char> ::= A | B | ... | Z
----
# decompose AND groups
goal ::= fullname
fullname ::= !push title fullname_0 | name | 
'''


class BNFParser(object):
    pass
