# -*- coding: utf-8 -*-
'''
Support library for unit-tests
'''

import unittest
import contextlib
import sys


@contextlib.contextmanager
def test_context(**context_vars):
    ''' Context manager support for variables used in tests
    '''
    try:
        yield
    except:
        sys.stderr.write('CONTEXT: {}\n'.format(str(context_vars)))
        raise

class OxeyeTest(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None  # show everything on failure
        super().setUp()

    def assertMatchPass(self, match, advance=None, args=None, kwargs=None):
        m_passfail, m_advance, m_args, m_kwargs = match
        if not m_passfail:
            raise self.failureException(f'Expected passing match: {match}')
        if advance is not None and m_advance != advance:
            raise self.failureException(
                    f'Match advance is not expected value: {m_advance} != {advance}')
        if args is not None and tuple(m_args) != tuple(args):
            raise self.failureException(
                    f'Match args is not expected value: {m_args} != {args}')
        if kwargs is not None and m_kwargs != kwargs:
            raise self.failureException(
                    f'Match kwargs is not expected value: {m_kwargs} != {kwargs}')

    def assertMatchFail(self, match):
        m_passfail, *_ = match
        if m_passfail:
            raise self.failureException(f'Expected failing match: {match}')

    def assertRulePass(self, result, advance=None, next_state=None):
        r_passfail, r_advance, r_next_state = result
        if not r_passfail:
            raise self.failureException(f'Expected passing rule: {result}')
        if advance is not None and r_advance != advance:
            raise self.failureException(
                    f'Rule advance is not expected value: {r_advance} != {advance}')
        if next_state is not None and r_next_state != next_state:
            raise self.failureException(
                    f'Rule next state is not expected value: {r_next_state} != {next_state}')

    def assertRuleFail(self, result):
        r_passfail, *_ = result
        if r_passfail:
            raise self.failureException(f'Expected failing match: {result}')

