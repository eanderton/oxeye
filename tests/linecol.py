from __future__ import unicode_literals, absolute_import

import unittest
from tests.helpers import *
from oxeye.linecol import pos_to_linecol


class TestLineCol(unittest.TestCase):
    def test_translate(self):
        text = 'hello\nworld\nfoo\nbar\nbaz\ngoat'
        self.assertEqual(pos_to_linecol(text, 10), (2, 4))
        self.assertEqual(pos_to_linecol(text, None), (6, 4))
        self.assertEqual(pos_to_linecol(text, 0), (1, 1))
