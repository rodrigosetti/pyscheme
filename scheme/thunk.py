#! coding: utf-8

class Thunk(object):
    """
    Thunks represent unevaluated objects. Created with the special form (delay
    <expression>). When evaluated, yield the evaluated expression
    """

    def __init__(self, expression, environment):
        self.expression = expression
        self.environment = environment
        self.is_evaluated = False

    def __repr__(self):
        return "<%s>" % self.expression

is_thunk = lambda x: isinstance(x, Thunk)

