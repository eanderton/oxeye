
from simpleparse import DFAParser

class AST(object):
    def __init__(self, left, right, op):
        self.left, self.right, self.op = left, right, op

    def debug(self):
        return { 
            'left': self.left.debug() if isinstance(self.left, AST) else self.left,
            'right': self.right.debug() if isinstance(self.right, AST) else self.right,
            'op': {
                float.__add__: '+',
                float.__sub__: '-',
                float.__mul__: '*',
                float.__div__: '/',
            }[self.op]
        }


class Calculator(object):

    def __init__(self):

        def insert(op):
            node = AST(self.head.right, None, op)
            self.head.right = node
            return node

        def arg(value):
            p = self.head
            if p.right:
                p = p.right
            p.right = float(value)

        def push_expr():
            self.stack.append(self.head)

        def pop_expr():
            self.head = self.stack.pop()

        def add():
            self.head = insert(float.__add__)

        def sub():
            self.head = insert(float.__sub__)

        def mul():
            insert(float.__mul__)

        def div():
            insert(float.__mul__)

        def err(msg):
            def impl():
                raise Exception(msg)
            return impl

        self.dfa = DFAParser({
            'expression': (
                (r'(\d+)', arg, 'operation'),
                (r'\(', push_expr, 'expression'),
                (r'.', err('Expected number or open-paren'), None),
            ),
            'operation': (
                (r'\+', add, 'expression'),
                (r'-', sub, 'expression'),
                (r'\*', mul, 'expression'),
                (r'/', div, 'expression'),
                (r'\)', pop_expr, 'operation'),
                (r'.', err('Expected numeric operation'), None),
            ),
        })

    def get_root(self):
        return self.root

    def __call__(self, text):
        self.root = AST(0.0, 0.0, float.__add__)
        self.head = self.root
        self.stack = []
        self.dfa.parse('expression', text)
     
        def traverse(node):
            if not isinstance(node, AST):
                return node
            left = traverse(node.left)
            right = traverse(node.right)
            result = node.op(left, right)
            print left, node.op, right, '=', result
            return result
        return traverse(self.root.right)  # eval to right to skip dummy root node

