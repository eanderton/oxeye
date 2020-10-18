# -*- coding: utf-8 -*-

import doctest
from oxeye.rule import *
from oxeye.exception import ParseError
from oxeye.testing import OxeyeTest

import oxeye.rule
doctest.testmod(oxeye.rule)


class RuleTest(OxeyeTest):
    def test_failed_rule(self):
        self.assertRuleFail(failed_rule())

    def test_passed_rule(self):
        self.assertRulePass(passed_rule(0, 'goal'))
        self.assertRulePass(passed_rule(123, 'goal'), 123, 'goal')

    def test_rule_next(self):
        rule = rule_next('next')
        self.assertRulePass(rule([]), 0, 'next')
        self.assertRulePass(rule(['foobar']), 0, 'next')

    def test_rule_fail(self):
        rule = rule_fail('some message')
        with self.assertRaises(ParseError, msg='some message'):
            rule([])
        with self.assertRaises(ParseError, msg='some message'):
            rule(['foo', 'bar'])
