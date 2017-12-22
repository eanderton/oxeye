import unittest

import simpleparse
from simpleparse import ParseError, DFAParser, pos_to_linecol
from calculator import Calculator
import json

class TestAdder(unittest.TestCase):
    def test_parse(self):
        calc = Calculator()

        self.assertEqual(calc(''), 0.0)

        for expr, result in (
            ('10', 10.0),
            ('10+11', 21.0),
            ('10+10-20', 00.0),
            ('10*11', 110.0),
            ('10+10*3', 40.0),
            ('(10)', 10.0),
            ('(10+11)', 21.0),
            ('(1+2)+(3+4)+(5+6)', 21.0),
            ('(10+10)-(20+40)', -40.0),
        ):
            test_result = calc(expr)
            print expr, json.dumps(calc.get_root().debug(), indent=4)
            self.assertEqual(test_result, result)


class TestLineCol(unittest.TestCase):
    def test_translate(self):
        text = 'hello\nworld\nfoo\nbar\nbaz\ngoat'
        self.assertEqual(pos_to_linecol(text, 10), (2, 4))
        self.assertEqual(pos_to_linecol(text, None), (6, 4))
        self.assertEqual(pos_to_linecol(text, 0), (1, 1))
