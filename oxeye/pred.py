# -*- coding: utf-8 -*-
'''
Standard predicates used for building grammars.
'''

def nop(*args, **kwargs):
    '''
    Predicate function that does nothing. Intended for do-nothing terminals in a DFA spec.
    '''
    pass


def err(message):
    '''
    Predicate function that emits an exception for `message`.
    '''
    def impl(*args, **kwargs):
        raise Exception(message)
    return impl



