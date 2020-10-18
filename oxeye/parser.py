# -*- coding: utf-8 -*-
'''
Oxeye Parser library.  Provides utility classes and functions for constructing
discrete state machines for parsing text or a token stream.
'''

from collections.abc import Callable
from collections.abc import Sequence
from functools import singledispatchmethod

from oxeye.exception import *
from oxeye.match import match_head, match_rex
from oxeye.pred import *
from oxeye.rule import failed_rule, passed_rule, rule_end

from pragma_utils import Singleton


class _EndState(Singleton):
    '''
    Representation of an 'end state' for a Parser.  Implemented
    as a singleton to avoid issues with cross-module imports.
    '''
    pass


EndState = _EndState()


class Parser(object):
    '''
    Core parser class.  Implements a token based parser based on a provided parser
    specification (`spec`).  The parser operates on an input set of tokens, that
    may be any indexable type, including `str`.

    '''

    _status_keys = ['pos', 'head', 'state', 'rule']

    def __init__(self, spec, start_state='goal', end_state=_EndState()):
        '''
        Parser constructor.  Builds a parser around the `spec` state machine that
        is a dictionary of state to rule-set mappings.  An optional `start_state`
        may be specified if 'goal' isn't a valid state in the provided spec.

        The parser specification is compiled into a series of closure functions by
        way of type-matching   Tuples, Dicts, and callables are valid
        rule types, each with their own special use cases and idioms.  The set of
        supported dispatch types may be expanded by augmenting or extending these
        multimethods.

        See the module documentation for more information on rules.
        '''

        self.spec = {
            end_state: [rule_end],
        }
        self._start_state = start_state
        self._state_refs = {}
        self.add_specification(spec, self)
        self.reset()

    def _parse_error(self, message):
        raise ParseError(message)

    @singledispatchmethod
    def _resolve_predicate(self, pred):
        raise CompileError(f'Cannot resolve predicate "{pred}"; is neither callable nor an attribute')

    @_resolve_predicate.register
    def _resolve_predicate_callable(self, pred: Callable):
        return pred

    @_resolve_predicate.register
    def _resolve_predicate_attr(self, pred: str):
        return getattr(self._context, pred)


    @singledispatchmethod
    def _compile_rule(self, rule):
        '''
        Default dispatch function for compiling rules.  Raises an exception as
        no other dispatchable types were matched.
        '''

        rule_type = type(rule)
        raise CompileError(self,
                f'No registered method to compile rule of type {rule_type}')

    @_compile_rule.register
    def _compile_rule_callable(self, rule: Callable):
        '''
        compiler dispatch function for callable rules.  Callables are allowed
        to simply pass-through to the compiled output.
        '''
        return rule


    @_compile_rule.register
    def _compile_rule_tuple(self, rule: Sequence):
        '''
        Compiler dispatch function for tuple-based rules.  Returns a function
        that processes zero or more tokens, and returns a passed/failed rule
        tuple as a result.
        '''

        match_tok, predicate, next_state = rule
        match_fn = self._compile_match(match_tok)
        predicate_fn = self._resolve_predicate(predicate)
        if not callable(match_fn):
            raise CompileError(self, 'Rule match function must compile to a callable object')
        
        def impl(sequence):
            match_success, advance, predicate_args, predicate_kwargs = match_fn(sequence)
            if match_success:
                predicate_fn(*predicate_args, **predicate_kwargs)
                return passed_rule(advance, next_state)
            return failed_rule()
        return impl

    @_compile_rule.register
    def _compile_rule_dict(self, rule_dict: dict):
        '''
        Compiler dispatch function for dict-based rules.  Returns a function
        that processes zero or more tokens, and returns a passed/failed rule
        tuple as a result.
        '''

        def impl(sequence):
            if len(sequence) == 0:
                return failed_rule()
            head = sequence[0]
            rule = rule_dict.get(head, None)
            if rule:
                predicate, next_state = rule
                predicate_fn = self._resolve_predicate(predicate)
                predicate_fn(head)
                return passed_rule(1, next_state)
            return failed_rule()
        return impl

    @singledispatchmethod
    def _compile_match(self, value):
        '''
        Default function for compiling match functions.  Raises an exception
        as no other dispatchable types were matched.
        '''

        raise CompileError(self, 'Match expression "{}" is not callable'.format(value))

    @_compile_match.register
    def _compile_match_callable(self, fn: Callable):
        '''
        Returns the provided match callable as a match function.
        '''
        return fn

    @_compile_match.register
    def _compile_match_str(self, value: str):
        '''
        Returns a match function for string values.
        '''
        return match_head(value)

    def reset(self):
        '''
        Clears any internal state, resetting the parser back to the initial
        parse state.
        '''

        self._state = self._start_state
        self._pos = 0
        self._seq = []
        self._rule = 0

    def add_specification(self, spec, context=None):
        '''
        Adds specification data to the parser.  May be called more than once to add
        additional parse states, and/or override existing ones.

        The context may be set for string predicate resolution.  This is useful for
        spec code management where the context object may be declared in a
        different scope than the spec itself.
        '''

        self._context = context or self
        for spec_state, tests in spec.items():
            self.spec[spec_state] = []
            for ii in range(len(tests)):
                rule = self._compile_rule(tests[ii])
                if not callable(rule):
                    raise CompileError(self,
                            f'Rule #{ii} of state {spec_state} must compile to a callable object')
                self.spec[spec_state].append(rule)
        self._context = None  # reset context

    def parse(self, sequence=None, state=None, position=0, exhaustive=True):
        '''
        Parses a sequence of elements, using the current state machine configuration.
        Each parameter overrides an aspect of this state, allowing for partial
        parse passes, starting from an alternate state or position, and running
        the parser to exhaustion.

        Returns True if the sequence was entirely parsed (exhausted), False if not.

        The default state, position, and sequence, in a newly constructed parser
        are set to `start_state`, `0`, and `[]` respectively.  Additionally, these
        are guaranteed by any call to `reset()`.

        The `exhaustive` argument is set to True by default.  The parser will
        raise ParseError if it cannot match a rule against the sequence in the
        current state. Exhaustive grammars must also match an `end` token as
        the last part of the grammar, as to ensure that the input completely
        matches the grammar.  See `oxeye.match.rule_end` for more information.

        Passing `sequence` will parse against the provided sequence, starting
        at the current position and state.

        Passing `state` will start the parse at the provided state instead of
        the current state.

        Passing `position` will start the parse at the provided position in the
        sequence instead of the current position.
        '''

        self._state = state if state is not None else self._state
        self._pos = position if position is not None else self._pos
        self._seq = sequence if sequence is not None else self._seq

        # walk through the state machine starting at state+pos+sequence
        while self._pos < len(self._seq):
            self._rule = 0
            for rule_fn in self.spec[self._state]:
                sub_sequence = self._seq[self._pos:]
                success, advance, next_state = rule_fn(sub_sequence)
                if success:
                    self._pos += advance
                    self._state = next_state
                    break
                self._rule += 1
            else:
                if exhaustive:
                    self._parse_error('No match found')
                return False

        # exit the state machine, and avoid 'end' matching
        if not exhaustive:
            return True

        # match 'end' token (empty sequence) in current state
        end_token = self._seq[0:0]
        for rule_fn in self.spec[self._state]:
            success, _, next_state = rule_fn(end_token)
            if success:
                return True
        self._parse_error('No match found at end of input')

    @property
    def pos(self):
        '''
        Returns a string for the current position of the parser.
        '''

        return self._pos

    @property
    def head(self):
        '''
        Returns the token at the current position of the parser.
        '''

        return self._seq[self._pos] if self._seq and self._pos < len(self._seq) else None

    @property
    def state(self):
        '''
        Returns the current state of the parser.
        '''

        return self._state

    @property
    def rule(self):
        '''
        Returns the rule index within the current state of the parser
        '''

        return self._rule

    @property
    def status(self):
        '''
        Returns a dict containing all the state values.  Suitable for use
        with `str.format()` as kwargs.
        '''

        return {x: getattr(self, x) for x in self._status_keys}


class RexParser(Parser):
    '''
    Parser implementation that treats all string match types as regular expressions.

    Overrides the match function compilation for `str` and maps them
    both to `match_rex()`.

    This parser will only accept string type sequences.
    '''

    @singledispatchmethod
    def _compile_match(self, *args, **kwargs):
        return super(RexParser, self)._compile_match(*args, **kwargs)

    @_compile_match.register
    def _compile_match_rex(self, tok: str):
        return match_rex(tok)

    def parse(self, sequence=None, state=None, position=0, exhaustive=True):
        if not isinstance(sequence, str):
            seq_type = type(sequence)
            self._parse_error(f'RexParser expects string or buffer (got {seq_type} instead)')
        super().parse(sequence, state, position, exhaustive)


class PositionMixin(object):
    '''
    Parser mixin class to support line and column handling.

    Integration will require calling the mixin methods directly
    from the desired points in the child class.  Two predicate
    functions, `_whitespace` and `_newline` are provided to
    allow a suitably configured grammar to manipulate the current
    line and column positions appropriately.

    >>> class MyParser(Parser, PositionMixin):
    >>>     _status_keys = Parser._status_keys + PositionMixin._position_status_keys
    >>>
    >>>     def reset(self):
    >>>         result = super().reset()
    >>>         self._reset_position
    '''

    _position_status_keys = ['line', 'column']

    def _reset_position(self):
        '''
            Resets the line and column
        '''

        self._line = 1
        self._column = 1

    def _next(self, value):
        '''
        Predicate function that increments the column count by value
        '''

        self._column += len(value)

    def _newline(self, value):
        '''
        Predicate function that increments the line by one, and resets the column to 1.
        '''

        self._column = 1
        self._line += 1

    @property
    def line(self):
        '''
        Returns the current token line positiion.
        '''

        return self._line

    @property
    def column(self):
        '''
        Returns the current token column position.
        '''

        return self._column

