# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import, print_function

import unittest
from examples.regex import RegularExpression
import json

class TestRegularExpression(unittest.TestCase):
    def test_regex_ctor(self):
        rex = RegularExpression()
        rex.compile('aaa|bbb')
        print('')
        print('Operands:', [str(x) for x in rex._operands])
        print('Operations:', [x.__name__ for x in rex._operations])

        rex.compile2()
        print('')
        print('Operands:', [str(x) for x in rex._operands])

