#! coding: utf-8

from cons import *

class Procedure(object):

    def __init__(self, parameters, body, environment):
        self.parameters = []

        # accumulate parameters, and optional variable-length, if any
        current = parameters
        while is_pair(current):
            self.parameters.append(car(current))
            current = cdr(current)
        self.optional = current

        self.body = body
        self.environment = environment

    def __repr__(self):
        # find out the procedure's name in this environment
        for key,value in self.environment.iteritems():
            if value == self:
                return "<compound procedure %s>" % key

        if self.optional:
            return "<compound procedure with minimum arity of %d>" % len(self.parameters)
        else:
            return "<compound procedure with arity %d>" % len(self.parameters)

class BuiltinProcedure(object):

    def __init__(self, callable_, name, min_args=None, max_args=None):
        self.callable_ = callable_
        self.name = name
        self.min_args = min_args
        self.max_args = max_args

    def __call__(self, args):
        len_args = 0 if args is None else len(args)
        if self.min_args is not None and len_args < self.min_args:
            raise ValueError("Built-in procedure %s should receive at least %d arguments. %d given." %
                             (self.name, self.min_args, len_args))
        elif self.max_args is not None and len_args > self.max_args:
            raise ValueError("Built-in procedure %s should receive at most %d arguments. %d given." %
                             (self.name, self.max_args, len_args))

        return self.callable_(args)

    def __repr__(self):
        return "<builtin procedure %s>" % self.name

