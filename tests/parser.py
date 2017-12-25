from __future__ import unicode_literals, absolute_import

import unittest
from oxeye import Token, ParseError, Parser
from tests.helpers import *


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
