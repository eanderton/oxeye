import unittest

import simpleparse
from simpleparse import Token, ParseError, Parser, TokenParser, RexParser, pos_to_linecol
import calculator
import sys
import json
import contextlib
import re

@contextlib.contextmanager
def test_context(**context_vars):
    try:
        yield
    except:
        sys.stderr.write('CONTEXT: {}\n'.format(str(context_vars)))
        raise


class TestToken(unittest.TestCase):
    def test_token_ctor(self):
        tok = Token('foobar', 'baz', 100, 200)
        self.assertEqual(tok.name, 'foobar')
        self.assertEqual(tok.value, 'baz')
        self.assertEqual(tok.line, 100)
        self.assertEqual(tok.column, 200)

    def test_factory_type(self):
        factory = Token.factory('foobar')
        self.assertEqual(str(factory), "<class 'simpleparse.token_foobar'>")

    def test_factory_create(self):
        factory = Token.factory('foobar')
        tok = factory('bar', 100, 200)
        self.assertEqual(tok.name, 'foobar')
        self.assertEqual(tok.value, 'bar')
        self.assertEqual(tok.line, 100)
        self.assertEqual(tok.column, 200)

    def test_factory_compare(self):
        foo_factory = Token.factory('foo')
        foo_tok = foo_factory('bar')
        bar_factory = Token.factory('bar')
        bar_tok = bar_factory('baz')

        self.assertEqual(type(foo_tok), foo_factory)
        self.assertEqual(type(bar_tok), bar_factory)

        self.assertNotEqual(type(foo_tok), bar_factory)
        self.assertNotEqual(type(bar_tok), foo_factory)


class TestParser(unittest.TestCase):
    def test_reset_custom_start(self):
        parser = Parser({}, 'foobar')
        self.assertEqual(parser.start_state, 'foobar')
        self.assertEqual(parser.state, 'foobar')
        parser.reset()
        self.assertEqual(parser.state, 'foobar')

    def test_reset_default_start(self):
        parser = Parser({})
        self.assertEqual(parser.start_state, 'goal')
        self.assertEqual(parser.state, 'goal')
        parser.reset()
        self.assertEqual(parser.state, 'goal')


class TestCalculator(unittest.TestCase):
    def test_lex(self):
        self.maxDiff = None  # show everything on failure
        Tok = calculator.Tok
        lexer = calculator.Lexer()

        for expr, result in (
            (' 10 ', [
                Tok.number(10.0, 1, 2)
            ]),
            ('-22.56 +\n*)(', [
                Tok.dash('-', 1, 1), 
                Tok.number('22.56', 1, 2),
                Tok.plus('+', 1, 8), 
                Tok.star('*', 2, 1), 
                Tok.rparen(')', 2, 2),
                Tok.lparen('(', 2, 3),
            ]),
        ):
            with test_context(expr=expr, result=result):
                lexer.reset()
                test_result = lexer.parse(expr)
                self.assertEqual(map(str, test_result), map(str, result))

    calc_tests = (
        ('', 0.0),
        (' 10', 10.0),
        ('10+11', 21.0),
        (' 10+ 10-20', 00.0),
        (' 10* 11', 110.0),
        ('10+10 * 3 ', 40.0),
        (' (10)', 10.0),
        ('(10+11)', 21.0),
        (' (1+2)+(3+4)+(5+6)', 21.0),
        (' ( 10+ 10) -(20+ 40) ', -40.0),
        ('3+0.14', 3.14),
        (' - 345', -345.0),
    )

    def test_rex_parse(self):
        calc = calculator.RexCalculator()
        for expr, result in self.calc_tests:
            with test_context(expr=expr, result=result):
                calc.reset()
                self.assertEqual(calc.dfa.state, 'ws_expression')
                self.assertEqual(result, calc.parse(expr).eval())

    def test_token_parse(self):
        calc = calculator.TokenCalculator()
        for expr, result in self.calc_tests:
            calc.reset()
            self.assertEqual(calc.dfa.state, 'expression')
            self.assertEqual(result, calc.parse(expr).eval())



class TestLineCol(unittest.TestCase):
    def test_translate(self):
        text = 'hello\nworld\nfoo\nbar\nbaz\ngoat'
        self.assertEqual(pos_to_linecol(text, 10), (2, 4))
        self.assertEqual(pos_to_linecol(text, None), (6, 4))
        self.assertEqual(pos_to_linecol(text, 0), (1, 1))
