from __future__ import unicode_literals, absolute_import

import unittest
from tests.helpers import *
from oxeye.parser import ParseError
from examples.calculator import Tok, Lexer, RexCalculator, TokenCalculator


class TestCalculator(unittest.TestCase):
    def test_lex(self):
        self.maxDiff = None  # show everything on failure
        lexer = Lexer()

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
        ('7 / 2', 3.5),
        (' - 345', -345.0),
    )

    def test_rex_parse(self):
        calc = RexCalculator()
        for expr, result in self.calc_tests:
            with test_context(expr=expr, result=result):
                calc.reset()
                self.assertEqual(calc.parser.state, 'ws_expression')
                self.assertEqual(result, calc.parse(expr).eval())

    def test_token_parse(self):
        calc = TokenCalculator()
        for expr, result in self.calc_tests:
            calc.reset()
            self.assertEqual(calc.parser.state, 'expression')
            self.assertEqual(result, calc.parse(expr).eval())

