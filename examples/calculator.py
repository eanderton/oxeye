from __future__ import unicode_literals, absolute_import

from oxeye.token import Token, TokenParser
from oxeye.parser import (Parser, RexParser, nop, err, 
                          match_any, match_peek, match_rex, match_all)


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


class RexCalculator(object):
    '''
    Example of a calculator that uses the RexParser as a basis for parsing.  
    All terminals and whitespace elimination are handled in the same pass,
    and matched explicitly using regular expressions.
    '''
    def __init__(self):
        self.ast = ASTManager()
        self.parser = RexParser({
            'ws_expression': (
                (r'\s+', nop, 'expression'),
                (match_peek, nop, 'expression'),
            ),
            'expression': (
                (r'-', self.ast.neg, 'ws_sub_expression'),
                (match_peek, nop, 'ws_sub_expression'),
            ),
            'ws_sub_expression': (
                (r'\s+', nop, 'sub_expression'),
                (match_peek, nop, 'sub_expression'),
            ),
            'sub_expression': (
                (r'(\d+(?:\.\d+)?)', self.ast.arg, 'ws_operation'),
                (r'\(', self.ast.push_expr, 'ws_expression'),
                (match_any, err('Expected number or open-param'), None),
            ),
            'ws_operation': (
                (r'\s+', nop, 'operation'),
                (match_peek, nop, 'operation'),
            ),
            'operation': (
                (r'\+', self.ast.add, 'ws_expression'),
                (r'-', self.ast.sub, 'ws_expression'),
                (r'\*', self.ast.mul, 'ws_expression'),
                (r'/', self.ast.div, 'ws_expression'),
                (r'\)', self.ast.pop_expr, 'ws_operation'),
                (match_any, err('Expected numeric operation'), None),
            ),
        }, start_state='ws_expression')

    def reset(self):
        self.ast.reset()
        self.parser.reset()

    def parse(self, text):
        self.parser.parse(text)
        return self.ast.root


# Token representing number values. 
tok_number = Token('number')

class Lexer(object):
    '''
    Lexer for TokenCalculator.  Seralizes a text stream into a list of tokens.
    Line and column information is gathered and attached to tokens as they are generated. 
    '''
    def __init__(self):
        def token(value, token_type=Token):
            #self.tokens.append(token_type(value, self.line, self.column))
            tok = token_type(value, line=self.line, column=self.column)
            self.tokens.append(tok)
            self.column += len(value)

        def number(value):
            token(value, tok_number)

        def ws(value):
            self.column += len(value)

        def newline(value):
            self.column = 1
            self.line += 1

        self.parser = Parser({
            'goal': (
                {
                    '(': (token, 'goal'),
                    ')': (token, 'goal'),
                    '-': (token, 'goal'),
                    '+': (token, 'goal'),
                    '*': (token, 'goal'),
                    '/': (token, 'goal'),
                    ' ': (ws, 'goal'),
                    '\r': (ws, 'goal'),
                    '\t': (ws, 'goal'),
                    '\v': (ws, 'goal'),
                    '\n': (newline, 'goal'),
                },
                (match_rex(r'(\d+(?:\.\d+)?)'), number, 'goal'),
                (match_any, err('unexpected token'), None),
            ),
        })
        self.reset()

    def reset(self):
        self.tokens = []
        self.line = 1
        self.column = 1
        self.parser.reset()

    def parse(self, text):
        self.parser.parse(text)


class TokenCalculator(object):
    '''
    Example of a calculator that uses a Token stream and Token matching for parsing.
    Relies on the Lexer implementation in this module to generate the input Token
    stream from the provided text.
    '''
    def __init__(self):
        self.ast = ASTManager()
        self.parser = TokenParser({
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
        self.parser.reset()
        self.ast.reset()
 
    def parse(self, text):
        lexer = Lexer()
        lexer.parse(text)
        self.parser.parse(lexer.tokens)
        return self.ast.root


