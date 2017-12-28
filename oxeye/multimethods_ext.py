# -*- coding: utf-8 -*-
'''
Multimethod extended support library
'''

from oxeye.multimethods import is_a, MultiMethod, Default


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
def _is_a_subclass(x, y):
    '''
    Multimethod that allows `Callable` to be used on type dispatch with 
    '''
    return callable(x)


def multimethod_extend(self, dispatch_func=None):
    '''
    Creates a new multimethod that extends this multimethod, by dispatching
    to this multimethod on default.  
    
    Can be called using an optional dispatch function `dispatch_func` for 
    the newly created multimethod.
    '''

    mm = MultiMethod(self.__name__, dispatch_func or self.dispatchfn, self.pass_self)
    mm.add_method(Default, lambda *a, **kw: self(*a, **kw))
    return mm


def patch_multimethod_extend():
    '''
    Monkeypatches a `MultiMethod.extend` method.  See documentation for
    `multimethod_extend()` for more information.
    '''
    MultiMethod.extend = multimethod_extend
