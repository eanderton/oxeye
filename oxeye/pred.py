# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import


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



