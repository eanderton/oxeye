# -*- coding: utf-8 -*-
'''
Multimethod extended support library
'''

from oxeye.multimethods import _copy_attrs, is_a, MultiMethod, Default
import copy
import inspect

class CallableType(object):
    '''
    Callable psuedo-type for multimethods.  The `Callable` instance may be
    used where type dispatch is desired to match on all callable types: classes,
    lambdas, and functions.
    '''

    def __repr__(self):
        return '<CallableType>'


Callable = CallableType()


@is_a.method((object, CallableType))
def _is_a_callable(x, y):
    '''
    Multimethod that allows `Callable` to be used on type dispatch with 
    '''
    if inspect.isclass(x):
        return callable(x.__dict__.get('__call__', None))
    return callable(x)


class StringType(object):
    '''
    String pseudo-type for multimethods.  The `String` instance may be used
    where type dispatch is desired to match on all string types: str, 
    and unicode.
    '''

    def __repr__(self):
        return '<StringType>'


String = StringType()


@is_a.method((object, StringType))
def _is_a_string(x, y):
    '''
    Multimethod that allows `String` to be used on type dispatch with 
    '''
    return x is str or x is unicode


def multimethod_clone(self):
    '''
    Creates a new multimethod that is a clone of this multimethod.
    '''
    return copy.deepcopy(self)


def patch_multimethod_clone():
    '''
    Monkeypatches a `MultiMethod.clone` method.  See documentation for
    `multimethod_clone()` for more information.
    '''
    MultiMethod.clone = multimethod_clone
