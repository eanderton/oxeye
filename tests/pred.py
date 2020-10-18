
# -*- coding: utf-8 -*-

import doctest
from oxeye.pred import *
from oxeye.exception import ParseError
from oxeye.testing import OxeyeTest

import oxeye.pred
doctest.testmod(oxeye.pred)


class PredTest(OxeyeTest):
    def test_nop(self):
        nop()
        nop('hello', 'world')
        nop(foo=1, bar=2)

    def test_err(self):
        pred = err('error message')
        with self.assertRaises(ParseError, msg='error message'):
            pred()
        with self.assertRaises(ParseError, msg='error message'):
            pred('hello', 'world', foo=1, bar=2)
