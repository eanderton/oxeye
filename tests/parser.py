from __future__ import unicode_literals, absolute_import

import unittest
from oxeye import *
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


class TestParserError(unittest.TestCase):
    def test_error_ctor(self):
        err = ParseError(0, 'foo', 'bar', 'baz')
        self.assertEqual(err.position, 0)
        self.assertEqual(err.state, 'foo')
        self.assertEqual(err.text, 'bar')
        self.assertEqual(err.message, 'baz')
        self.assertIsNone(err.nested_exception)
        
    def test_error_ctor_nested(self):
        nested = Exception('nested')
        err = ParseError(0, 'foo', 'bar', 'baz', nested)
        self.assertEqual(err.position, 0)
        self.assertEqual(err.state, 'foo')
        self.assertEqual(err.text, 'bar')
        self.assertEqual(err.message, 'baz')
        self.assertIs(err.nested_exception, nested)

    def test_parse_error(self):
        nested = Exception('test')
        def throw_fn(value):
            raise nested

        p = Parser({
            'goal': (
                (match_str('foo'), throw_fn, 'goal'),
                (match_str('baz'), err('failure'), 'goal'),
            )
        })

        with self.assertRaises(ParseError) as ctx:
            p.parse('bar')
        e = ctx.exception
        self.assertEquals(e.message, 'No match found')

        with self.assertRaises(ParseError) as ctx:
            p.parse('foo')
        e = ctx.exception
        self.assertEquals(e.message, 'test')
        self.assertEquals(e.nested_exception, nested)
        
        with self.assertRaises(ParseError) as ctx:
            p.parse('baz')
        e = ctx.exception
        self.assertEquals(e.message, 'failure')


class TestMatchFunction(unittest.TestCase):
    def setUp(self):
        self.all_value = None
        self.any_value = None
        self.peek_value = None
        self.range_value = None
 
        def all_pred(values):
            self.all_value = values
 
        def any_pred(value):
            self.any_value = value
 
        def peek_pred(value):
            self.peek_value = value
 
        def range_pred(value):
            self.range_value = value
 
        self.parser = Parser({
            'any': (
                (match_any, any_pred, 'all'),
            ),
            'peek': (
                (match_peek, peek_pred, 'all'),
            ),
            'range_digit': (
                (match_range(map(str, range(0, 9))), range_pred, 'all'),
            ),
            'range_char': (
                (match_range(['f', 'b']), range_pred, 'all'),
            ),
            'range_str': (
                (match_range(['foo', 'bar']), range_pred, 'all'),
            ),
            'all': (
                (match_all, all_pred, None),
            ),
        }, 'all')
     
    def test_match_all(self):
        self.parser.parse('foobar', 'all')
        self.assertEquals(self.all_value, 'foobar')

    def test_match_any(self):
        self.parser.parse('foobar', 'any')
        self.assertEquals(self.any_value, 'f')
        self.assertEquals(self.all_value, 'oobar')

    def test_match_peek(self):
        self.parser.parse('foobar', 'peek')
        self.assertEquals(self.peek_value, 'f')
        self.assertEquals(self.all_value, 'foobar')

    def test_match_range_digit(self):
        self.parser.parse('1234', 'range_digit')
        self.assertEquals(self.range_value, '1')
        self.assertEquals(self.all_value, '234')
        
    def test_match_range_char(self):
        self.parser.parse('foobar', 'range_char')
        self.assertEquals(self.range_value, 'f')
        self.assertEquals(self.all_value, 'oobar')

    def test_match_range_str(self):
        self.parser.parse(['foo', 'bar'], 'range_str')
        self.assertEquals(self.range_value, 'foo')
        self.assertEquals(self.all_value, ['bar'])
