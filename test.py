import unittest

import simpleparse
from simpleparse import ParseError, Parser, TokenParser, RexParser, pos_to_linecol
import calculator
import sys
import json
import contextlib

@contextlib.contextmanager
def test_context(**context_vars):
    try:
        yield
    except:
        sys.stderr.write('CONTEXT: {}\n'.format(str(args), str(context_vars)))
        raise


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
        Tok = calculator.Tok
        lexer = calculator.Lexer()

        for expr, result in (
            (' 10 ', [Tok.number.copy(10.0)]),
            ('-22.56 +\n*)(', [Tok.dash, Tok.number.copy(22.56), Tok.plus, Tok.star, Tok.rparen, Tok.lparen]),
        ):
            with test_context(expr=expr, result=result):
                lexer.reset()
                test_result = lexer.parse(expr)
                self.assertEqual(test_result, result)

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
