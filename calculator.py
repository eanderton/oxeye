
from simpleparse import DFAParser, nop


class AST(object):

    def __init__(self, left, right, op):
        self.left, self.right, self.op = left, right, op

    @classmethod
    def traverse(cls, node):
        if not isinstance(node, AST):
            return node
        left = AST.traverse(node.left)
        right = AST.traverse(node.right)
        result = node.op(left, right)
        print left, node.op, right, '=', result
        return result

    def debug(self):
        return { 
            'left': self.left.debug() if isinstance(self.left, AST) else self.left,
            'right': self.right.debug() if isinstance(self.right, AST) else self.right,
            'op': str(self.op),
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

        def neg():
            # AST assumes binary operations, so a shim is needed
            self.head = insert(lambda a,b: float.__neg__(b))

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
                (r'-', neg, 'sub_expression'),
                (r'(?=.)', nop, 'sub_expression'),
            ),
            'sub_expression': (
                (r'(\d+(?:\.\d+)?)', arg, 'operation'),
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

    def __call__(self, text):
        self.root = AST(0.0, 0.0, float.__add__)
        self.head = self.root
        self.stack = []
        self.dfa.parse('expression', text)
        return AST.traverse(self.root.right)  # eval right to skip dummy root node

