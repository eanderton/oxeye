
from __future__ import unicode_literals, absolute_import

import unittest
from tests.helpers import *
from oxeye.parser import ParseError
from examples.bnf import Tok, BnfLexer #, BnfParser

class TestLexer(unittest.TestCase):
    def setUp(self):
        self.lexer = BnfLexer()

    def assertTokensEqual(self, a, b):
        self.assertEqual(map(unicode, a), map(unicode, b)) 

    def test_lex0(self):
        self.lexer.parse('hello world')
        self.assertTokensEqual(self.lexer.tokens, [
            Tok.ident('hello', 1, 1), Tok.ident('world', 1, 7)
        ])


class TestParser(unittest.TestCase):
    def setUp(self):
        self.parser = BnfParser()

    def assertASTEqual(self, a, b):
        self.assertEqual(unicode(a), unicode(b))
