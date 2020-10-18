# -*- coding: utf-8 -*-

import unittest
from examples.regex import RegularExpression
from oxeye.testing import *
import json

class TestRegularExpression(OxeyeTest):
    def test_regex_ctor(self):
        rex = RegularExpression()
        rex.compile('aaa|bbb')
        print('')
        print('Operands:', [str(x) for x in rex._operands])
        print('Operations:', [x.__name__ for x in rex._operations])

        rex.compile2()
        print('')
        print('Operands:', [str(x) for x in rex._operands])

