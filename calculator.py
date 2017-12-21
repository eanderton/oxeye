
from simpleparse import DFAParser
from collections import namedtuple

class Calculator(object):
    def __init__(self):
        class AST(object):
            def __init__(self, left, right, op):
                self.left, self.right, self.op = left, right, op

        def arg(value):
            self.root.right = float(value)

        def push_expr():
            self.stack.append(self.root)

        def pop_expr():
            self.stack.pop(self.root)

        def add():
            self.ops.append(float.__add__)

        def sub():
            self.ops.append(float.__sub__)

        def mul():
            root.op = 
            # (...) * x
            self.ops.insert(len(self.ops)-1, float.__mul__)

        def div():
            self.ops.insert(len(self.ops)-1, float.__div__)

        self.dfa = DFAParser({
            'expression': (
                (r'(\d+)', arg, 'operation'),
                (r'\(', push_expr, 'expression'),
                (r'\)', pop_expr, 'expression'),
            ),
            'operation': (
                (r'\+', add, 'expression'),
                (r'-', sub, 'expression'),
                (r'\*', mul, 'expression'),
                (r'/', div, 'expression'),
            ),
        })

    def __call__(self, text):
        self.root = AST(0, 0, float.__add__)
        self.stack = []
        self.dfa.parse('expression', text)
     
        def traverse(node):
            left, right, op = root
            if left instanceof AST:
                left = traverse(left)
            if right instanceof AST:
                right = traverse(right)
            return op(left, right)
        return traverse(self.root)

