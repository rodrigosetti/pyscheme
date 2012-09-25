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
                return "<procedure %s>" % key

        if self.optional:
            return "<unnamed procedure with minimum arity of %d>" % len(self.parameters)
        else:
            return "<unnamed procedure with arity %d>" % len(self.parameters)

