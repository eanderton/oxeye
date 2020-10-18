# -*- coding: utf-8 -*-

import doctest
import unittest
import copy
from oxeye.parser import *
from oxeye.match import *
from oxeye.rule import *
from oxeye.testing import *

import oxeye.parser
doctest.testmod(oxeye.parser)


# TODO: test parser continuation

class TestParser(OxeyeTest):
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


class TestParserCompile(OxeyeTest):
    def test_invalid_rule(self):
        with self.assertRaises(CompileError,
                msg='No registered method to compile rule'):
            class BadObject(object): pass
            Parser({
                'foo': [BadObject()]
            })

    def test_invalid_rule_compile(self):
        with self.assertRaises(CompileError,
                msg='Rule must compile to a callable object'):
            class BadParser(Parser):
                _compile_rule = copy.deepcopy(Parser._compile_rule)

                @_compile_rule.register
                def _compile_rule_str(self, rule: str):
                    return rule  # pass-through to trigger exception

            BadParser({
                'foo': [ 'bar', ]
            })

    def test_callable_rule_compile(self):
        rule = lambda x: None
        p = Parser({
            'foo': [ rule ]
        })
        self.assertEqual(p.spec['foo'][0], rule)

    def test_invalid_match_fn(self):
        with self.assertRaises(CompileError,
                msg='Match expression "12345" is not callable'):
            Parser({
                'foo': [ (12345, lambda x: None, 'foo'), ]
            })

    def test_invalid_match_compile(self):
        with self.assertRaises(CompileError,
                msg='Rule match function must compile to a callable object'):
            class BadParser(Parser):
                _compile_match = copy.deepcopy(Parser._compile_match)

                @_compile_match.register
                def _compile_rule_str(self, rule: int):
                    return rule  # pass-through to trigger exception

            BadParser({
                'foo': [ (12345, lambda x: None, 'foo'), ]
            })

    def test_implicit_end(self):
        p = Parser({
            'goal': (
                (match_seq('foobar'), nop, EndState),
            ),
        })
        p.parse('foobar')

    def test_explicit_end(self):
        p = Parser({
            'goal': (
                (match_seq('foobar'), nop, 'goal'),
                rule_end,
            ),
        })
        p.parse('foobar')

    def test_custom_end(self):
        p = Parser({
            'goal': (
                (match_seq('foobar'), nop, 'end'),
            ),
        }, end_state='end')
        p.parse('foobar')


class TestParserError(OxeyeTest):
    def setUp(self):
        def throw_fn(value):
            raise Exception('test')

        self.parser = Parser({
            'goal': (
                (match_seq('foo'), throw_fn, 'goal'),
                (match_seq('baz'), err('failure'), 'goal'),
            )
        })

    def test_parse_error1(self):
        with self.assertRaises(ParseError,
                msg='No match found'):
            self.parser.parse('bar')
        self.assertEqual(self.parser.status, {
            'pos': 0,
            'head': 'b',
            'state': 'goal',
            'rule': 2,
        })

    def test_parse_error2(self):
        with self.assertRaises(Exception,
                msg='test'):
            self.parser.parse('foo')
        self.assertEqual(self.parser.status, {
            'pos': 0,
            'head': 'f',
            'state': 'goal',
            'rule': 0,
        })

    def test_parse_error3(self):
        with self.assertRaises(ParseError,
                msg='failure'):
            self.parser.parse('baz')
        self.assertEqual(self.parser.status, {
            'pos': 0,
            'head': 'b',
            'state': 'goal',
            'rule': 1,
        })


class TestMatchFunction(OxeyeTest):
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
                (match_all, all_pred, 'all'),
                rule_end,
            ),
        }, 'all')

    def test_match_all(self):
        self.parser.parse('foobar', 'all')
        self.assertEqual(self.all, 'foobar')

    def test_match_any(self):
        self.parser.parse('foobar', 'any')
        self.assertEqual(self.result, 'f')
        self.assertEqual(self.all, 'oobar')

    def test_match_peek(self):
        self.parser.parse('foobar', 'peek')
        self.assertEqual(self.result, 'f')
        self.assertEqual(self.all, 'foobar')

    def test_match_set_digit(self):
        self.parser.parse('1234', 'range_digit')
        self.assertEqual(self.result, '1')
        self.assertEqual(self.all, '234')

    def test_match_set_char(self):
        self.parser.parse('foobar', 'range_char')
        self.assertEqual(self.result, 'f')
        self.assertEqual(self.all, 'oobar')

    def test_match_set_str(self):
        self.parser.parse(['foo', 'bar'], 'range_str')
        self.assertEqual(self.result, 'foo')
        self.assertEqual(self.all, ['bar'])

    def test_match_seq_char(self):
        self.parser.parse('foobar', 'sequence_char')
        self.assertEqual(self.result, 'foo')
        self.assertEqual(self.all, 'bar')

    def test_match_seq_str(self):
        self.parser.parse(['foo', 'bar', 'baz'], 'sequence_str')
        self.assertEqual(self.result, ['foo', 'bar'])
        self.assertEqual(self.all, ['baz'])


class TestRexParser(OxeyeTest):
    def test_rex_ctor_fail(self):
        with self.assertRaises(ParseError,
                msg='RexParser expects string or buffer (got [] instead)'):
            RexParser({}).parse([])
