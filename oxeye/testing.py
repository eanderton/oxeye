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

    def assertLexEqual(self, a, b):
        self.assertEqual(map(str, a), map(str, b))

    def assertMatchPass(self, match, advance=None, args=None, kwargs=None):
        m_state, m_advance, m_args, m_kwargs = match
        if not m_state:
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
        m_state, *_ = match
        if m_state:
            raise self.failureException(f'Expected failing match: {match}')

