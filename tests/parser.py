from __future__ import unicode_literals, absolute_import

import unittest
from oxeye.parser import *
from tests.helpers import *

# TODO: test parser continuation

class TestParser(unittest.TestCase):
    def test_reset_custom_start(self):
        parser = Parser({}, 'foobar')
        self.assertEqual(parser._start_state, 'foobar')
        self.assertEqual(parser.state, 'foobar')
        parser.reset()
        self.assertEqual(parser.state, 'foobar')

    def test_reset_default_start(self):
        parser = Parser({})
        self.assertEqual(parser._start_state, 'goal')
        self.assertEqual(parser.state, 'goal')
        parser.reset()
        self.assertEqual(parser.state, 'goal')


class TestParserCompile(unittest.TestCase):
    def test_invalid_rule(self):
        with self.assertRaises(CompileError) as ctx:
            Parser({
                'foo': [ 'bar', ]
            })
        self.assertEquals(ctx.exception.message, 'No registered method to compile rule')

    def test_invalid_rule_compile(self):
        with self.assertRaises(CompileError) as ctx:
            class BadParser(Parser):
                _compile_rule = Parser._compile_rule.clone()
                
                @_compile_rule.method(unicode)
                @_compile_rule.method(str)
                def _compile_rule_str(self, rule):
                    return rule  # pass-through to trigger exception

            BadParser({
                'foo': [ 'bar', ]
            })
        self.assertEquals(ctx.exception.message, 'Rule must compile to a callable object')

    def test_callable_rule_compile(self):
        rule = lambda x: None
        p = Parser({
            'foo': [ rule ]
        })
        self.assertEquals(p.spec['foo'][0], rule) 

    def test_invalid_match_fn(self):
        with self.assertRaises(CompileError) as ctx:
            Parser({
                'foo': [ (12345, lambda x: None, 'foo'), ]
            })
        self.assertEquals(ctx.exception.message, 'Match expression "12345" is not callable')

    def test_invalid_match_compile(self):
        with self.assertRaises(CompileError) as ctx:
            class BadParser(Parser):
                _compile_match = Parser._compile_match.clone()
                
                @_compile_match.method(int)
                def _compile_rule_str(self, rule):
                    return rule  # pass-through to trigger exception

            BadParser({
                'foo': [ (12345, lambda x: None, 'foo'), ]
            })
        self.assertEquals(ctx.exception.message, 'Rule match function must compile to a callable object')


class TestParserError(unittest.TestCase):
    def setUp(self):
        def throw_fn(value):
            raise Exception('test')

        self.parser = Parser({
            'goal': (
                (match_seq('foo'), throw_fn, 'goal'),
                (match_seq('baz'), err('failure'), 'goal'),
            )
        })

    def test_error_ctor(self):
        err = ParseError('foobar')
        self.assertEqual(err.message, 'foobar')
        
    def test_parse_error1(self):
        with self.assertRaises(ParseError) as ctx:
            self.parser.parse('bar')
        e = ctx.exception
        self.assertEquals(self.parser.status, {
            'pos': 0,
            'head': 'b',
            'state': 'goal',
            'rule': 2,
        })
        self.assertEquals(e.message, 'No match found')

    def test_parse_error2(self):
        with self.assertRaises(Exception) as ctx:
            self.parser.parse('foo')
        e = ctx.exception
        self.assertEquals(self.parser.status, {
            'pos': 0,
            'head': 'f',
            'state': 'goal',
            'rule': 0,
        })
        self.assertEquals(e.message, 'test')
        
    def test_parse_error3(self):
        with self.assertRaises(Exception) as ctx:
            self.parser.parse('baz')
        e = ctx.exception
        self.assertEquals(self.parser.status, {
            'pos': 0,
            'head': 'b',
            'state': 'goal',
            'rule': 1,
        })
        self.assertEquals(e.message, 'failure')


class TestMatchFunction(unittest.TestCase):
    def setUp(self):
        self.all = None
        self.result = None

        def all_pred(value):
            self.all = value
 
        def result_pred(value):
            self.result = value
 
        self.parser = Parser({
            'any': (
                (match_any, result_pred, 'all'),
            ),
            'peek': (
                (match_peek, result_pred, 'all'),
            ),
            'range_digit': (
                (match_set(map(str, range(0, 9))), result_pred, 'all'),
            ),
            'range_char': (
                (match_set(['f', 'b']), result_pred, 'all'),
            ),
            'range_str': (
                (match_set(['foo', 'bar']), result_pred, 'all'),
            ),
            'sequence_char': (
                (match_seq('foo'), result_pred, 'all'),
            ),
            'sequence_str': (
                (match_seq(['foo', 'bar']), result_pred, 'all'),
            ),
            'all': (
                (match_all, all_pred, None),
            ),
        }, 'all')
     
    def test_match_all(self):
        self.parser.parse('foobar', 'all')
        self.assertEquals(self.all, 'foobar')

    def test_match_any(self):
        self.parser.parse('foobar', 'any')
        self.assertEquals(self.result, 'f')
        self.assertEquals(self.all, 'oobar')

    def test_match_peek(self):
        self.parser.parse('foobar', 'peek')
        self.assertEquals(self.result, 'f')
        self.assertEquals(self.all, 'foobar')

    def test_match_set_digit(self):
        self.parser.parse('1234', 'range_digit')
        self.assertEquals(self.result, '1')
        self.assertEquals(self.all, '234')
         
    def test_match_set_char(self):
        self.parser.parse('foobar', 'range_char')
        self.assertEquals(self.result, 'f')
        self.assertEquals(self.all, 'oobar')

    def test_match_set_str(self):
        self.parser.parse(['foo', 'bar'], 'range_str')
        self.assertEquals(self.result, 'foo')
        self.assertEquals(self.all, ['bar'])

    def test_match_seq_char(self):
        self.parser.parse('foobar', 'sequence_char')
        self.assertEquals(self.result, 'foo')
        self.assertEquals(self.all, 'bar')

    def test_match_seq_str(self):
        self.parser.parse(['foo', 'bar', 'baz'], 'sequence_str')
        self.assertEquals(self.result, ['foo', 'bar'])
        self.assertEquals(self.all, ['baz'])


class TestRexParser(object):
    def test_rex_ctor_fail(self):
        with self.assertRaises(Exception) as ctx:
            RexParser([])
        self.assertEquals(e.message, 'RexParser expects string or buffer (got [] instead)')
