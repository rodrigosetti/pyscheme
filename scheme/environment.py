# coding: utf-8

import codecs
import operator
import sys

from cons import *
from procedure import BuiltinProcedure

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

def make_minimum_environment():
    env = Environment()

    # utf-8 stdin and out
    stdin = codecs.getreader('utf-8')(sys.stdin)
    stdout = codecs.getreader('utf-8')(sys.stdout)

    env.update({
            'nil' : None,
            '#t' : True,
            '#f' : False,
            'atom?': BuiltinProcedure(lambda args: is_atom(car(args)), 'atom?', 1, 1),
            '=':     BuiltinProcedure(lambda args: car(args) == cadr(args), '=', 2, 2),
            'eq?':   BuiltinProcedure(lambda args: car(args) is cadr(args), 'eq?', 2, 2),
            'car':   BuiltinProcedure(lambda args: caar(args), 'car', 1, 1),
            'cdr':   BuiltinProcedure(lambda args: cdar(args), 'cdr', 1, 1),
            'cons':  BuiltinProcedure(lambda args: cons(car(args), cadr(args)), 'cons', 2, 2),
            'write': BuiltinProcedure(lambda args: stdout.write(car(args).encode('utf-8').decode('string_escape')), 'write', 1, 1),
            'read':  BuiltinProcedure(lambda args: stdin.read(1), 'read', 0, 0),
            'file-open':  BuiltinProcedure(lambda args: codecs.open(car(args), cadr(args), 'utf-8'), 'file-open', 2, 2),
            'file-close': BuiltinProcedure(lambda args: car(args).close(), 'file-close', 1, 1),
            'file-write': BuiltinProcedure(lambda args: car(args).write(cadr(args).encode('utf-8').decode('string_escape').decode('utf-8')), 'file-write', 2, 2),
            'file-read':  BuiltinProcedure(lambda args: car(args).read(1), 'file-read', 1, 1),
            })
    return env

def make_default_environment():

    env = make_minimum_environment()
    env.update({
            '+':     BuiltinProcedure(lambda args: reduce(operator.add, args), '+', 2),
            '-':     BuiltinProcedure(lambda args: reduce(operator.sub, args), '-', 2),
            '*':     BuiltinProcedure(lambda args: reduce(operator.mul, args), '*', 2),
            '/':     BuiltinProcedure(lambda args: reduce(operator.div, args), '/', 2),
            'mod':   BuiltinProcedure(lambda args: reduce(operator.mod, args), 'mod', 2),
            '<':     BuiltinProcedure(lambda args: car(args) <  cadr(args), '<',  2),
            '>':     BuiltinProcedure(lambda args: car(args) >  cadr(args), '>',  2),
            '<=':    BuiltinProcedure(lambda args: car(args) <= cadr(args), '<=', 2),
            '>=':    BuiltinProcedure(lambda args: car(args) >= cadr(args), '>=', 2),
            'or':    BuiltinProcedure(lambda args: any(args), 'or', 2),
            'not':   BuiltinProcedure(lambda args: not any(args), 'not', 1),
            'and':   BuiltinProcedure(lambda args: all(args), 'and', 2),
            'list':  BuiltinProcedure(lambda args: args, 'list'),
            'len':   BuiltinProcedure(lambda args: 0 if is_nil(car(args)) else len(car(args)), 'len', 1, 1),
            'nil?':  BuiltinProcedure(lambda args: is_nil(car(args)), 'nil?', 1, 1),
            'cons?': BuiltinProcedure(lambda args: is_pair(car(args)), 'cons', 1, 1),
            '!=':    BuiltinProcedure(lambda args: car(args) != cadr(args), '!=', 2, 2),
        })
    return env
