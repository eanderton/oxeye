from __future__ import unicode_literals, absolute_import

import contextlib
import sys


@contextlib.contextmanager
def test_context(**context_vars):
    try:
        yield
    except:
        sys.stderr.write('CONTEXT: {}\n'.format(str(context_vars)))
        raise

