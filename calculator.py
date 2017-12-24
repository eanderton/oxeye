
from simpleparse import (Token, RexParser, TokenParser, nop, err, match_any, match_peek, 
                        match_range, match_all)
from collections import namedtuple



class Tok(Token):
    pass


Tok.number = Tok('number')
Tok.lparen = Tok('lparen')
Tok.rparen = Tok('rparen')
Tok.dash = Tok('dash')
Tok.plus = Tok('plus')
Tok.star = Tok('star')
Tok.slash = Tok('slash')


class Lexer(object):
    '''
    Lexer for Calculator implementation.  Seralizes a text stream into a list of tokens.
    '''
    def __init__(self):
        def a(tok):
            def impl():
                self.column += 1
                new_tok = tok.copy()
                new_tok.line = self.line
                new_tok.column = self.column
                self.tokens.append(new_tok)
            return impl

        def number(value):
            new_tok = Tok.number.copy(float(value))
            new_tok.line = self.line
            new_tok.column = self.column
            self.tokens.append(Tok.number.copy(float(value)))

        def new_line(value):
            self.column = 1
            self.line += 1

        self.dfa = RexParser({
            'goal': (
                (r'\s+', nop, 'goal'),  # discard all whitespace 
                (r'(\d+(?:\.\d+)?)', number, 'goal'),
                (r'\(', a(Tok.lparen), 'goal'),
                (r'\)', a(Tok.rparen), 'goal'),
                (r'-', a(Tok.dash), 'goal'),
                (r'\+', a(Tok.plus), 'goal'),
                (r'\*', a(Tok.star), 'goal'),
                (r'/', a(Tok.slash), 'goal'),
                (r'\n', new_line, 'goal'),
                (match_any, err('unexpected token'), None),
            ),
        })
        self.reset()

    def reset(self):
        self.tokens = []
        self.line = 1
        self.column = 1

    def parse(self, text):
        self.dfa.parse(text)
        return self.tokens


class AST(object):
    '''
    Abstract syntax tree representation for the calculator.
    '''
    def __init__(self, left, right, op):
        self.left, self.right, self.op = left, right, op

    def eval(self):
        return AST.traverse(self)

    @classmethod
    def traverse(cls, node):
        if not isinstance(node, AST):
            return node
        return node.op(AST.traverse(node.left), AST.traverse(node.right))


class CalculatorBase(object):
    '''
    Arithemtic expression calculator.
    '''

    def _insert(self, op):
        node = AST(self.head.right, None, op)
        self.head.right = node
        return node

    def _arg(self, value):
        p = self.head
        if p.right:
            p = p.right
        p.right = float(value)

    def _push_expr(self, *args):
        self.stack.append(self.head)

    def _pop_expr(self, *args):
        self.head = self.stack.pop()

    def _neg(self, *args):
        # AST assumes binary operations, so a shim is needed
        self.head = self._insert(lambda a,b: float.__neg__(b))

    def _add(self, *args):
        self.head = self._insert(float.__add__)

    def _sub(self, *args):
        self.head = self._insert(float.__sub__)

    def _mul(self, *args):
        self._insert(float.__mul__)

    def _div(self, *args):
        self._insert(float.__mul__)

    def reset(self):
        self.root = AST(0.0, 0.0, float.__add__)
        self.head = self.root
        self.stack = []
        self.dfa.reset()


class RexCalculator(CalculatorBase):
    def __init__(self):
        self.dfa = RexParser({
            'ws_expression': (
                (r'\s+', nop, 'expression'),
                (match_peek, nop, 'expression'),
            ),
            'expression': (
                (r'-', self._neg, 'ws_sub_expression'),
                (match_peek, nop, 'ws_sub_expression'),
            ),
            'ws_sub_expression': (
                (r'\s+', nop, 'sub_expression'),
                (match_peek, nop, 'sub_expression'),
            ),
            'sub_expression': (
                (r'(\d+(?:\.\d+)?)', self._arg, 'ws_operation'),
                (r'\(', self._push_expr, 'ws_expression'),
                (match_any, err('Expected number or open-param'), None),
            ),
            'ws_operation': (
                (r'\s+', nop, 'operation'),
                (match_peek, nop, 'operation'),
            ),
            'operation': (
                (r'\+', self._add, 'ws_expression'),
                (r'-', self._sub, 'ws_expression'),
                (r'\*', self._mul, 'ws_expression'),
                (r'/', self._div, 'ws_expression'),
                (r'\)', self._pop_expr, 'ws_operation'),
                (match_any, err('Expected numeric operation'), None),
            ),
        }, start_state='ws_expression')
        self.reset()

    def parse(self, text):
        self.dfa.parse(text)
        return self.root


class TokenCalculator(CalculatorBase):
    def __init__(self):
        self.dfa = TokenParser({
            'expression': (
                (Tok.dash, self._neg, 'sub_expression'),
                (match_peek, nop, 'sub_expression'),
            ),
            'sub_expression': (
                (Tok.number, self._arg, 'operation'),
                (Tok.lparen, self._push_expr, 'expression'),
                (match_any, err('Expected number or open-paren'), None),
            ),
            'operation': (
                (Tok.plus, self._add, 'expression'),
                (Tok.dash, self._sub, 'expression'),
                (Tok.star, self._mul, 'expression'),
                (Tok.slash, self._div, 'expression'),
                (Tok.rparen, self._pop_expr, 'operation'),
                (match_any, err('Expected numeric operation'), None),
            ),
        }, start_state='expression')
        self.reset()

    def parse(self, text):
        self.dfa.parse(Lexer().parse(text))
        return self.root


