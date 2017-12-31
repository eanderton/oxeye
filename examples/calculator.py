from __future__ import unicode_literals, absolute_import

from oxeye.token import Token, TokenParser, TokenLexer
from oxeye.parser import Parser, RexParser, nop, err
from oxeye.match import match_any, match_peek, match_rex, match_all
#from oxeye.rule import rule_err, rule_next

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


class ASTManager(object):
    '''
    Tracks abstract syntax tree state for Calculator expressions
    '''
    def __init__(self):
        self.reset()

    def insert(self, op):
        node = AST(self.head.right, None, op)
        self.head.right = node
        return node

    def arg(self, value):
        if isinstance(value, Token):
            value = value.value
        p = self.head
        if p.right:
            p = p.right
        p.right = float(value)

    def push_expr(self, *args):
        self.stack.append(self.head)

    def pop_expr(self, *args):
        self.head = self.stack.pop()

    def neg(self, *args):
        # AST assumes binary operations, so a shim is needed
        self.head = self.insert(lambda a,b: float.__neg__(b))

    def add(self, *args):
        self.head = self.insert(float.__add__)

    def sub(self, *args):
        self.head = self.insert(float.__sub__)

    def mul(self, *args):
        self.insert(float.__mul__)

    def div(self, *args):
        self.insert(float.__div__)

    def reset(self):
        self.root = AST(0.0, 0.0, float.__add__)
        self.head = self.root
        self.stack = []


class RexCalculator(RexParser):
    '''
    Example of a calculator that uses the RexParser as a basis for parsing.  
    All terminals and whitespace elimination are handled in the same pass,
    and matched explicitly using regular expressions.
    '''
    def __init__(self):
        self.ast = ASTManager()
        super(RexCalculator, self).__init__({
            'expression': (
                (r'\s+', nop, 'expression'),
                (r'-', self.ast.neg, 'sub_expression'),
                (match_peek, nop, 'sub_expression'),
            ),
            'sub_expression': (
                (r'\s+', nop, 'sub_expression'),
                (r'(\d+(?:\.\d+)?)', self.ast.arg, 'operation'),
                (r'\(', self.ast.push_expr, 'expression'),
                (match_any, err('Expected number or open-param'), None),
            ),
            'operation': (
                (r'\s+', nop, 'operation'),
                (r'\+', self.ast.add, 'expression'),
                (r'-', self.ast.sub, 'expression'),
                (r'\*', self.ast.mul, 'expression'),
                (r'/', self.ast.div, 'expression'),
                (r'\)', self.ast.pop_expr, 'operation'),
                (match_any, err('Expected numeric operation'), None),
            ),
        }, start_state='expression')

    def reset(self):
        self.ast.reset()
        super(RexParser, self).reset()

    def parse(self, text):
        super(RexParser, self).parse(text)
        return self.ast.root


# Token representing number values. 
tok_number = Token('number')

class Lexer(TokenLexer):
    '''
    Lexer for TokenCalculator.  Seralizes a text stream into a list of tokens.
    Line and column information is gathered and attached to tokens as they are generated. 
    '''
    def __init__(self):
        super(TokenLexer, self).__init__({
            'goal': (
                {
                    '(': (self._token, 'goal'),
                    ')': (self._token, 'goal'),
                    '-': (self._token, 'goal'),
                    '+': (self._token, 'goal'),
                    '*': (self._token, 'goal'),
                    '/': (self._token, 'goal'),
                    ' ': (self._whitespace, 'goal'),
                    '\r': (self._whitespace, 'goal'),
                    '\t': (self._whitespace, 'goal'),
                    '\v': (self._whitespace, 'goal'),
                    '\n': (self._newline, 'goal'),
                },
                (match_rex(r'(\d+(?:\.\d+)?)'), self._token_as(tok_number), 'goal'),
                (match_any, err('unexpected token'), None),
            ),
        })


class TokenCalculator(TokenParser):
    '''
    Example of a calculator that uses a Token stream and Token matching for parsing.
    Relies on the Lexer implementation in this module to generate the input Token
    stream from the provided text.
    '''
    def __init__(self):
        self.ast = ASTManager()
        super(TokenCalculator, self).__init__({
            'expression': (
                ('-', self.ast.neg, 'sub_expression'),
                (match_peek, nop, 'sub_expression'),
            ),
            'sub_expression': (
                {
                    tok_number: (self.ast.arg, 'operation'),
                    '(': (self.ast.push_expr, 'expression'),
                },
                (match_any, err('Expected number or open-paren'), None),
            ),
            'operation': (
                {
                    '+': (self.ast.add, 'expression'),
                    '-': (self.ast.sub, 'expression'),
                    '*': (self.ast.mul, 'expression'),
                    '/': (self.ast.div, 'expression'),
                    ')': (self.ast.pop_expr, 'operation'),
                },
                (match_any, err('Expected numeric operation'), None),
            ),
        }, start_state='expression')

    def reset(self):
        super(TokenCalculator, self).reset()
        self.ast.reset()
 
    def parse(self, text):
        lexer = Lexer()
        lexer.parse(text)
        super(TokenCalculator, self).parse(lexer.tokens)
        return self.ast.root


