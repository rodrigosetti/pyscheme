# coding: utf-8

import operator
from cons import *

class Environment(dict):
    """
    Hierarchical dictionary
    """

    def __init__(self, parent=None):
        self.parent = parent

    def __getitem__(self, name):
        """
        Get expression evaluated from the hierarchy
        """
        try:
            return super(Environment, self).__getitem__(name)
        except KeyError as e:
            if self.parent is not None:
                return self.parent[name]
            else:
                raise e

    def change(self, name, value):
        if name in self:
            self[name] = value
        elif self.parent is None:
            raise KeyError("%s not found in environment" % name)
        else:
            self.parent.change(name, value)

def make_global_environment():

    env = Environment()
    env.update({
            'nil' : None,
            '+': lambda args: reduce(operator.add, args),
            '-': lambda args: reduce(operator.sub, args),
            '*': lambda args: reduce(operator.mul, args),
            '/': lambda args: reduce(operator.div, args),
            'mod': lambda args: reduce(operator.mod, args),
            '<': lambda args: car(args) < cadr(args),
            '>': lambda args: car(args) > cadr(args),
            '<=': lambda args: car(args) <= cadr(args),
            '>=': lambda args: car(args) >= cadr(args),
            'or': lambda args: any(args),
            'not': lambda args: not any(args),
            'and': lambda args: all(args),
            'list': lambda args: args,
            'len': lambda args: 0 if is_nil(car(args)) else len(car(args)),
            'nil?': lambda args: is_nil(car(args)),
            'atom?': lambda args: is_atom(car(args)),
            'cons?': lambda args: is_pair(car(args)),
            '=': lambda args: car(args) == cadr(args),
            '!=': lambda args: car(args) != cadr(args),
            'eq?': lambda args: car(args) is cadr(args),
            'car': lambda args: caar(args),
            'cdr': lambda args: cdar(args),
            'cons': lambda args: cons(car(args), cadr(args)),
        })
    return env
