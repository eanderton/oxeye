from __future__ import unicode_literals, absolute_import

from oxeye.parser import (Token, RexParser, TokenParser, nop, err, match_any, match_peek, 
                        match_range, match_all)


class Tok(object):
    '''
    Containing namespace for token types.
    '''
    number = Token.factory('number', float)
    lparen = Token.factory('lparen')
    rparen = Token.factory('rparen')
    dash = Token.factory('dash')
    plus = Token.factory('plus')
    star = Token.factory('star')
    slash = Token.factory('slash')


class Lexer(object):
    '''
    Lexer for TokenCalculator.  Seralizes a text stream into a list of tokens.
    Line and column information is gathered and attached to tokens as they are generated. 
    '''
    def __init__(self):
        def tt(token_type):
            def impl(value):
                self.tokens.append(token_type(value, self.line, self.column))
                self.column += len(value)
            return impl

        def ws(value):
            self.column += len(value)

        def new_line(value):
            self.column = 1
            self.line += 1

        self.parser = RexParser({
            'goal': (
                (r'(\n)', new_line, 'goal'),
                (r'(\s+)', ws, 'goal'),
                (r'(\d+(?:\.\d+)?)', tt(Tok.number), 'goal'),
                (r'(\()', tt(Tok.lparen), 'goal'),
                (r'(\))', tt(Tok.rparen), 'goal'),
                (r'(-)', tt(Tok.dash), 'goal'),
                (r'(\+)', tt(Tok.plus), 'goal'),
                (r'(\*)', tt(Tok.star), 'goal'),
                (r'(/)', tt(Tok.slash), 'goal'),
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
        self.insert(float.__mul__)

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
                (Tok.dash, self.ast.neg, 'sub_expression'),
                (match_peek, nop, 'sub_expression'),
            ),
            'sub_expression': (
                (Tok.number, self.ast.arg, 'operation'),
                (Tok.lparen, self.ast.push_expr, 'expression'),
                (match_any, err('Expected number or open-paren'), None),
            ),
            'operation': (
                (Tok.plus, self.ast.add, 'expression'),
                (Tok.dash, self.ast.sub, 'expression'),
                (Tok.star, self.ast.mul, 'expression'),
                (Tok.slash, self.ast.div, 'expression'),
                (Tok.rparen, self.ast.pop_expr, 'operation'),
                (match_any, err('Expected numeric operation'), None),
            ),
        }, start_state='expression')

    def reset(self):
        self.parser.reset()
        self.ast.reset()
 
    def parse(self, text):
        self.parser.parse(Lexer().parse(text))
        return self.ast.root

