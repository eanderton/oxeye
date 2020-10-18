# -*- coding: utf-8 -*-
import unittest
from oxeye.parser import ParseError
from oxeye.token import Token
from oxeye.testing import *
from examples.calculator import Lexer, RexCalculator, TokenCalculator


class TestLexer(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None  # show everything on failure
        self.lexer = Lexer()

    def test_lex1(self):
        self.lexer.parse(' 10 ')
        expected = [
            Token('number', '10', 1, 2)
        ]
        self.assertEqual(self.lexer.tokens, expected)

    def test_lex2(self):
        self.lexer.parse('- 22.56 +\n*)(')
        expected = [
            Token('-', '-', 1, 1),
            Token('number', '22.56', 1, 3),
            Token('+', '+', 1, 9),
            Token('*', '*', 2, 1),
            Token(')', ')', 2, 2),
            Token('(', '(', 2, 3),
        ]
        self.assertEqual(self.lexer.tokens, expected)


class TestCalculator(unittest.TestCase):
    def setUp(self):
        self.rexCalc = RexCalculator()
        self.tokCalc = TokenCalculator()

    def test_parse1(self):
        expr = ''
        result = 0.0
        self.assertEqual(result, self.rexCalc.parse(expr).eval())
        self.assertEqual(result, self.tokCalc.parse(expr).eval())

    def test_parse2(self):
        expr = ' 10'
        result = 10.0
        self.assertEqual(result, self.rexCalc.parse(expr).eval())
        self.assertEqual(result, self.tokCalc.parse(expr).eval())

    def test_parse3(self):
        expr = '10+11'
        result = 21.0
        self.assertEqual(result, self.rexCalc.parse(expr).eval())
        self.assertEqual(result, self.tokCalc.parse(expr).eval())

    def test_parse4(self):
        expr = ' 10+ 10-20'
        result = 00.0
        self.assertEqual(result, self.rexCalc.parse(expr).eval())
        self.assertEqual(result, self.tokCalc.parse(expr).eval())

    def test_parse3(self):
        expr = '10+11'
        result = 21.0
        (' 10* 11', 110.0),
        self.assertEqual(result, self.rexCalc.parse(expr).eval())
        self.assertEqual(result, self.tokCalc.parse(expr).eval())

    def test_parse4(self):
        expr = ' 10+ 10-20'
        result = 00.0
        self.assertEqual(result, self.rexCalc.parse(expr).eval())
        self.assertEqual(result, self.tokCalc.parse(expr).eval())

    def test_parse5(self):
        expr = ' 10+ 10-20'
        result = 00.0
        self.assertEqual(result, self.rexCalc.parse(expr).eval())
        self.assertEqual(result, self.tokCalc.parse(expr).eval())

    def test_parse6(self):
        expr = '10+10 * 3 '
        result = 40.0
        self.assertEqual(result, self.rexCalc.parse(expr).eval())
        self.assertEqual(result, self.tokCalc.parse(expr).eval())

    def test_parse7(self):
        expr = ' (10)'
        result = 10.0
        self.assertEqual(result, self.rexCalc.parse(expr).eval())
        self.assertEqual(result, self.tokCalc.parse(expr).eval())

    def test_parse8(self):
        expr = '(10+11)'
        result = 21.0
        self.assertEqual(result, self.rexCalc.parse(expr).eval())
        self.assertEqual(result, self.tokCalc.parse(expr).eval())

    def test_parse9(self):
        expr = ' (1+2)+(3+4)+(5+6)'
        result = 21.0
        self.assertEqual(result, self.rexCalc.parse(expr).eval())
        self.assertEqual(result, self.tokCalc.parse(expr).eval())

    def test_parse10(self):
        expr = ' ( 10+ 10) -(20+ 40) '
        result = -40.0
        self.assertEqual(result, self.rexCalc.parse(expr).eval())
        self.assertEqual(result, self.tokCalc.parse(expr).eval())

    def test_parse11(self):
        expr = '3+0.14'
        result = 3.14
        self.assertEqual(result, self.rexCalc.parse(expr).eval())
        self.assertEqual(result, self.tokCalc.parse(expr).eval())

    def test_parse12(self):
        expr = '7 / 2'
        result = 3.5
        self.assertEqual(result, self.rexCalc.parse(expr).eval())
        self.assertEqual(result, self.tokCalc.parse(expr).eval())

    def test_parse13(self):
        expr = ' - 345'
        result = -345.0
        self.assertEqual(result, self.rexCalc.parse(expr).eval())
        self.assertEqual(result, self.tokCalc.parse(expr).eval())

