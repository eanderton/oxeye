
from simpleparse import Token, RexParser, TokenParser, nop, err
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
    """
    Lexer for Calculator implementation.  Seralizes a text stream into a list of tokens.
    """
    def __init__(self):
        def a(tok):
            def impl():
                self.tokens.append(tok)
            return impl

        def number(value):
            self.tokens.append(Tok.number(float(value)))

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
                RexParser.err_state('unexpected token'),
            ),
        })
        self.reset()

    def reset(self):
        self.tokens = []

    def parse(self, text):
        self.dfa.parse('goal', text)
        return self.tokens


class AST(object):
    """
    Abstract syntax tree representation for the calculator.
    """
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
    """
    Arithemtic expression calculator.
    """

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

    def reset(self, *args):
        self.root = AST(0.0, 0.0, float.__add__)
        self.head = self.root
        self.stack = []


class RexCalculator(CalculatorBase):
    def __init__(self):
        self.dfa = RexParser({
            'ws_expression': (
                (r'\s+', nop, 'expression'),
                RexParser.next_state('expression'),
            ),
            'expression': (
                (r'-', self._neg, 'ws_sub_expression'),
                RexParser.next_state('ws_sub_expression'),
            ),
            'ws_sub_expression': (
                (r'\s+', nop, 'sub_expression'),
                RexParser.next_state('sub_expression'),
            ),
            'sub_expression': (
                (r'(\d+(?:\.\d+)?)', self._arg, 'ws_operation'),
                (r'\(', self._push_expr, 'ws_expression'),
                RexParser.err_state('Expected number or open-paren'),
            ),
            'ws_operation': (
                (r'\s+', nop, 'operation'),
                RexParser.next_state('operation'),
            ),
            'operation': (
                (r'\+', self._add, 'ws_expression'),
                (r'-', self._sub, 'ws_expression'),
                (r'\*', self._mul, 'ws_expression'),
                (r'/', self._div, 'ws_expression'),
                (r'\)', self._pop_expr, 'ws_operation'),
                RexParser.err_state('Expected numeric operation'),
            ),
        })
        self.reset()

    def parse(self, text):
        self.dfa.parse('ws_expression', text)
        return self.root


class TokenCalculator(CalculatorBase):
    def __init__(self):
        self.dfa = TokenParser({
            'expression': (
                (Tok.dash, self._neg, 'sub_expression'),
                TokenParser.next_state('sub_expression'),
            ),
            'sub_expression': (
                (Tok.number, self._arg, 'operation'),
                (Tok.lparen, self._push_expr, 'expression'),
                TokenParser.err_state('Expected number or open-paren'),
            ),
            'operation': (
                (Tok.plus, self._add, 'expression'),
                (Tok.dash, self._sub, 'expression'),
                (Tok.star, self._mul, 'expression'),
                (Tok.slash, self._div, 'expression'),
                (Tok.rparen, self._pop_expr, 'operation'),
                TokenParser.err_state('Expected numeric operation'),
            ),
        })
        self.reset()

    def parse(self, text):
        self.dfa.parse('expression', Lexer().parse(text))
        return self.root


