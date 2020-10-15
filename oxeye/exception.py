# -*- coding: utf-8 -*-
'''
Exception classes for use with Oxeye grammars.
'''

class ParseError(Exception):
    '''
    Base error type for parse related errors.  May optionally include a nested
    exception if another exception was the cause for the error.

    See the parser `status` property for additional error context.
    '''
    pass


class CompileError(Exception):
    '''
    Error type for compilation-based errors.

    See the parser `status` property for additional error context.
    '''
    def __init__(self, parser, *args, **kwargs):
        super(CompileError, self).__init__(*args, **kwargs)
        self.parser = parser


