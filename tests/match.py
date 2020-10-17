# -*- coding: utf-8 -*-
import doctest
import oxeye.match
from oxeye.match import *
from oxeye.testing import OxeyeTest

doctest.testmod(oxeye.match)


class MatchTest(OxeyeTest):
    def test_failed_match(self):
        self.assertMatchFail(failed_match())

    def test_passed_match(self):
        self.assertMatchPass(passed_match(0))
        self.assertMatchPass(passed_match(1), 1)
        self.assertMatchPass(passed_match(2, ('foo',)), 2, ('foo',))
        self.assertMatchPass(passed_match(3, ('foo',), {'a':'b'}),
                3, ('foo',), {'a':'b'})

    def test_match_any(self):
        self.assertMatchFail(match_any([]))
        self.assertMatchPass(match_any(['foobar']), 1, ('foobar',))
        self.assertMatchPass(match_any(['foo', 'bar']), 1, ('foo',))

    def test_match_peek(self):
        self.assertMatchFail(match_peek([]))
        self.assertMatchPass(match_peek(['foobar']), 0, ('foobar',))
        self.assertMatchPass(match_peek(['foo', 'bar']), 0, ('foo',))

    def test_match_set(self):
        empty_set = match_set([])
        self.assertMatchFail(empty_set([]))
        self.assertMatchFail(empty_set(['foo', 'bar']))

        multi_set = match_set(['a','b','c'])
        self.assertMatchFail(multi_set(['x']))
        self.assertMatchPass(multi_set(['a']), 1, ('a',))
        self.assertMatchPass(multi_set(['b']), 1, ('b',))
        self.assertMatchPass(multi_set(['c']), 1, ('c',))

    def test_match_all(self):
        self.assertMatchFail(match_all([]))
        self.assertMatchPass(match_all(['a']), 1, [['a']])
        self.assertMatchPass(match_all(['a','b','c']), 3, [['a','b','c']])

    def test_match_head(self):
        matcher = match_head('a')
        self.assertMatchFail(matcher([]))
        self.assertMatchFail(matcher(['x']))
        self.assertMatchPass(matcher(['a']), 1, ['a'])
        self.assertMatchPass(matcher(['a','b','c']), 1, ['a'])

    def test_match_seq(self):
        matcher = match_seq(['a'])
        self.assertMatchFail(matcher([]))
        self.assertMatchFail(matcher(['x']))
        self.assertMatchPass(matcher(['a']), 1, [['a']])
        self.assertMatchPass(matcher(['a','b','c']), 1, [['a']])

        matcher = match_seq(['a','b','c'])
        self.assertMatchFail(matcher([]))
        self.assertMatchFail(matcher(['x']))
        self.assertMatchPass(matcher(['a','b','c']), 3, [['a','b','c']])
        self.assertMatchPass(matcher(['a','b','c','d']), 3, [['a','b','c']])

        matcher = match_seq('foo')
        self.assertMatchFail(matcher(''))
        self.assertMatchFail(matcher('x'))
        self.assertMatchPass(matcher('foo'), 3, ['foo'])
        self.assertMatchPass(matcher('foobar'), 3, ['foo'])

    def matxh_rex(self):
        matcher = match_rex('foo')
        self.assertMatchFail(matcher(''))
        self.assertMatchFail(matcher('x'))
        self.assertMatchPass(matcher('foo'), 3, ['foo'])
        self.assertMatchPass(matcher('foobar'), 3, ['foo'])

        matcher = match_rex('f(oo)')
        self.assertMatchFail(matcher(''))
        self.assertMatchFail(matcher('x'))
        self.assertMatchPass(matcher('foo'), 3, ['oo'])
        self.assertMatchPass(matcher('foobar'), 3, ['oo'])

        matcher = match_rex('f(?P<xx>oo)')
        self.assertMatchFail(matcher(''))
        self.assertMatchFail(matcher('x'))
        self.assertMatchPass(matcher('foo'), 3, [], {'xx':'oo'})
        self.assertMatchPass(matcher('foobar'), 3, [], {'xx':'oo'})

    def match_end(self):
        self.assertMatchPass(match_end([]))
        self.assertMatchFail(match_end(['a', 'b', 'c']))
        self.assertMatchFail(match_end('foobar'))
