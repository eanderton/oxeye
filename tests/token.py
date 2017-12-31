from __future__ import unicode_literals, absolute_import

import unittest
from oxeye.parser import nop
from oxeye.token import *
from tests.helpers import *


class TestToken(unittest.TestCase):
    def test_token_ctor(self):
        tok = Token('foobar', 'baz', 100, 200)
        self.assertEqual(tok.name, 'foobar')
        self.assertEqual(tok.value, 'baz')
        self.assertEqual(tok.line, 100)
        self.assertEqual(tok.column, 200)

    def test_factory_create(self):
        factory = Token.factory('foobar')
        tok = factory('bar', 100, 200)
        self.assertEqual(tok.name, 'foobar')
        self.assertEqual(tok.value, 'bar')
        self.assertEqual(tok.line, 100)
        self.assertEqual(tok.column, 200)

    def test_factory_create(self):
        foo_factory = Token('foo')
        foo_tok = foo_factory('bar')
        bar_factory = Token('bar')
        bar_tok = bar_factory('baz')

        self.assertEqual(foo_tok.name, foo_factory.name)
        self.assertEqual(bar_tok.name, bar_factory.name)

        self.assertNotEqual(foo_tok.name, bar_factory.name)
        self.assertNotEqual(bar_tok.name, foo_factory.name)

    def test_token_hash(self):
        a = Token('foo')
        b = Token('foo')

        self.assertEqual(hash(a), hash('foo'))
        self.assertEqual(hash(a), hash(b))

    def test_token_lookup(self):
        a = Token('foo')
        b = Token('bar')
        x = {
            a: 'a',
            b: 'b',
        }
        self.assertEqual(x[a], 'a')
        self.assertEqual(x[b], 'b')

        a = Token('foo')
        b = Token('bar')
        self.assertEqual(x[a], 'a')
        self.assertEqual(x[b], 'b')

    def test_str_lookup(self):
        a = Token('foo')
        b = Token('bar')
        x = {
            'foo': 'a',
            'bar': 'b',
        }
        self.assertEqual(x[a], 'a')
        self.assertEqual(x[b], 'b')


class TestTokenLexer(unittest.TestCase):
    def test_status(self):
        def ws(value):
            p._whitespace(value)

        def newline(value):
            p._newline(value)

        p = TokenLexer({
            'goal': (
                ('f', nop, 'goal'),
                ('o', nop, 'goal'),
                ('b', nop, 'goal'),
                ('a', nop, 'goal'),
                ('r', nop, 'goal'),
                ('\n', newline, 'goal'),
                (' ', ws, 'goal'),
            )
        })
        p.parse('foo \nbar \nbaz\ngorf', exhaustive=False)
        self.assertEqual('({line},{column})'.format(**p.status), '(3,1)')
   
    
class TestTokenParser(unittest.TestCase):
    def test_match_token(self):
        result = None
        def result_pred(value):
            result = value

        p = TokenParser({
            'goal': (
                (Token('foo'), result_pred, 'goal'),
            )
        })
        self.assertTrue(p.parse([Token('foo')]))
        
    def test_status(self):
        p = TokenParser({
            'goal': (
                ('foo', nop, 'goal'),
            )
        })
        p.parse([
            Token('foo', line=1, column=2), Token('bar', line=10, column=20),
        ], exhaustive=False)
        self.assertEqual('({line},{column})'.format(**p.status), '(10,20)')

